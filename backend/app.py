import os
import uuid
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from models import Base, Product, CartItem, get_engine_and_session
from db_init import recreate_database
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

# Config
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "projeto_emeece")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# recria o DB
if os.getenv("DEV_RESET_DB", "true").lower() == "true":
    recreate_database()

engine, Session = get_engine_and_session(DB_USER, DB_PASS, DB_HOST, DB_NAME)
Base.metadata.create_all(engine)

app = Flask(__name__)
CORS(app)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

def calc_cart_total(session, cart_id: str) -> float:
    total = session.query(func.coalesce(func.sum(CartItem.unit_price * CartItem.qty), 0.0))\
                   .filter(CartItem.cart_id == cart_id).scalar() or 0.0
    return float(total)

# Produtos
@app.route("/api/products", methods=["GET"])
def list_products():
    session = Session()
    products = session.query(Product).all()
    out = [{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "stock_qty": p.stock_qty,
        "image": p.image
    } for p in products]
    session.close()
    return jsonify(out)

@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    session = Session()
    p = session.get(Product, product_id)
    if not p:
        session.close()
        return jsonify({"error": "Produto não encontrado"}), 404
    out = {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "stock_qty": p.stock_qty,
        "image": p.image
    }
    session.close()
    return jsonify(out)

@app.route("/api/products", methods=["POST"])
def upsert_product():
    data = request.json or {}
    required = ["id", "name", "price", "stock_qty"]
    for k in required:
        if k not in data:
            return jsonify({"error": f"Campo obrigatório: {k}"}), 400
    pid = int(data["id"])

    session = Session()
    p = session.get(Product, pid)
    if not p:
        p = Product(
            id=pid,
            name=data["name"],
            description=data.get("description"),
            price=float(data["price"]),
            stock_qty=int(data["stock_qty"]),
            image=data.get("image")
        )
        session.add(p)
    else:
        p.name = data["name"]
        p.description = data.get("description")
        p.price = float(data["price"])
        p.stock_qty = int(data["stock_qty"])
        p.image = data.get("image", p.image)
        session.add(p)

    session.commit()
    session.close()
    return jsonify({"message": "Produto salvo"}), 200

@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Remove produto e quaisquer itens do carrinho que o referenciem."""
    session = Session()
    try:
        prod = session.get(Product, product_id)
        if not prod:
            session.close()
            return jsonify({"error": "Produto não encontrado"}), 404

        session.query(CartItem).filter(CartItem.product_id == product_id)\
               .delete(synchronize_session=False)

        session.delete(prod)
        session.commit()
        session.close()
        return jsonify({"message": "Produto removido"}), 200
    except SQLAlchemyError:
        session.rollback()
        session.close()
        return jsonify({"error": "Erro ao remover produto"}), 500

# upload de imagem
@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "Arquivo não enviado"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nome de arquivo vazio"}), 400
    filename = secure_filename(file.filename)
    final_name = f"{uuid.uuid4().hex}_{filename}"
    path = os.path.join(UPLOAD_FOLDER, final_name)
    file.save(path)
    return jsonify({"filename": final_name})

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)

# Carrinho
@app.route("/api/cart/add", methods=["POST"])
def add_to_cart():
    """
    Espera JSON: { cart_id?: string, product_id: number, qty: number }
    Regra: não adiciona se estoque == 0; qty não pode exceder estoque atual.
    """
    data = request.json or {}
    cart_id = data.get("cart_id") or str(uuid.uuid4())
    product_id = int(data["product_id"])
    qty = max(1, int(data.get("qty", 1)))

    session = Session()
    product = session.get(Product, product_id)
    if not product:
        session.close()
        return jsonify({"error": "Produto não encontrado"}), 404

    if product.stock_qty <= 0:
        session.close()
        return jsonify({"error": "Produto esgotado"}), 400

    if qty > product.stock_qty:
        session.close()
        return jsonify({"error": "Quantidade solicitada acima do estoque", "max_qty": product.stock_qty}), 400

    it = session.query(CartItem).filter(
        CartItem.cart_id == cart_id, CartItem.product_id == product_id
    ).one_or_none()

    if it:
        new_qty = min(it.qty + qty, product.stock_qty)
        it.qty = new_qty
        it.max_qty = product.stock_qty
        session.add(it)
    else:
        it = CartItem(
            cart_id=cart_id,
            product_id=product.id,
            product_name=product.name,
            unit_price=product.price,
            qty=qty,
            max_qty=product.stock_qty
        )
        session.add(it)

    session.commit()
    session.close()
    return jsonify({"message": "Adicionado ao carrinho", "cart_id": cart_id}), 200

@app.route("/api/cart/<string:cart_id>", methods=["GET"])
def get_cart(cart_id):
    session = Session()
    items = session.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    out = []
    total = 0.0
    for it in items:
        # incluir imagem do produto
        image = it.product.image if it.product else None
        subtotal = float(it.unit_price) * int(it.qty)
        total += subtotal
        out.append({
            "id": it.id,
            "product_id": it.product_id,
            "product_name": it.product_name,
            "unit_price": float(it.unit_price),
            "qty": int(it.qty),
            "max_qty": int(it.max_qty),
            "subtotal": float(subtotal),
            "image": image
        })
    session.close()
    return jsonify({"items": out, "total": float(total)})

@app.route("/api/cart/item/<int:item_id>", methods=["PUT"])
def update_cart_item(item_id):
    data = request.json or {}
    new_qty = int(data.get("qty", 1))
    if new_qty < 1:
        return jsonify({"error": "Quantidade mínima é 1"}), 400

    session = Session()
    it = session.get(CartItem, item_id)
    if not it:
        session.close()
        return jsonify({"error": "Item não encontrado"}), 404

    product = session.get(Product, it.product_id)
    if not product:
        session.close()
        return jsonify({"error": "Produto não encontrado"}), 404

    if new_qty > product.stock_qty:
        session.close()
        return jsonify({"error": "Quantidade solicitada acima do estoque", "max_qty": product.stock_qty}), 400

    it.qty = new_qty
    it.max_qty = product.stock_qty
    session.add(it)

    cart_total = calc_cart_total(session, it.cart_id)
    session.commit()
    session.close()
    return jsonify({"message": "Quantidade atualizada", "item_id": item_id, "cart_total": cart_total}), 200

@app.route("/api/cart/item/<int:item_id>", methods=["DELETE"])
def delete_cart_item(item_id):
    session = Session()
    it = session.get(CartItem, item_id)
    if not it:
        session.close()
        return jsonify({"error": "Item não encontrado"}), 404
    session.delete(it)
    session.commit()
    session.close()
    return jsonify({"message": "Item removido"}), 200

@app.route("/api/cart/checkout", methods=["POST"])
def checkout():
    """
    Espera JSON: { cart_id: string, shipping: "padrao" | "expresso" }
    Passos: valida estoque, debita estoque, soma total produtos + frete, limpa carrinho.
    """
    data = request.json or {}
    cart_id = data.get("cart_id")
    shipping = data.get("shipping", "padrao")

    if not cart_id:
        return jsonify({"error": "cart_id obrigatório"}), 400

    FRETES = {"padrao": 10.0, "expresso": 25.0}
    if shipping not in FRETES:
        return jsonify({"error": "Tipo de frete inválido"}), 400
    frete = FRETES[shipping]

    session = Session()
    items = session.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    if not items:
        session.close()
        return jsonify({"error": "Carrinho vazio"}), 400

    for it in items:
        product = session.get(Product, it.product_id)
        if not product:
            session.close()
            return jsonify({"error": f"Produto {it.product_id} não encontrado"}), 400
        if it.qty > product.stock_qty:
            session.close()
            return jsonify({"error": f"Estoque insuficiente para '{product.name}'", "max_qty": product.stock_qty}), 400

    total_products = 0.0
    for it in items:
        product = session.get(Product, it.product_id)
        product.stock_qty -= it.qty
        total_products += float(it.unit_price) * int(it.qty)
        session.add(product)

    total = total_products + float(frete)

    session.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
    session.commit()
    session.close()

    return jsonify({
        "message": "Pedido finalizado com sucesso",
        "total_products": float(total_products),
        "frete": float(frete),
        "total": float(total)
    }), 200

@app.route("/")
def index():
    return jsonify({
        "message": "🚀 Servidor Flask do projeto_emeece está rodando!",
        "endpoints": {
            "Listar produtos": "/api/products",
            "Carrinho": "/api/cart/<cart_id>",
            "Upload de imagem": "/api/upload"
        }
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
