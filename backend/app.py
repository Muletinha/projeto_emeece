import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from models import Product, CartItem, get_engine_and_session, Base
from db_init import recreate_database
from sqlalchemy.exc import NoResultFound
import uuid
from werkzeug.utils import secure_filename

# configuração banco
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "projeto_emeece")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# recria o DB só se variável de ambiente DEV_RESET_DB=true (banco é recriado a todo momento que o código é iniciado)
if os.getenv("DEV_RESET_DB", "true").lower() == "true":
    recreate_database()

engine, Session = get_engine_and_session(DB_USER, DB_PASS, DB_HOST, DB_NAME)
Base.metadata.create_all(engine)

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

# table produtos
@app.route("/api/products", methods=["GET"])
def list_products():
    session = Session()
    products = session.query(Product).all()
    out = []
    for p in products:
        out.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "stock_qty": p.stock_qty,
            "image": p.image
        })
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

# Upsert: se id existe, atualiza se não, cria (o usuário fornece id)
@app.route("/api/products", methods=["POST"])
def create_or_update_product():
    data = request.json
    # Espera: id, name, description, price, stock_qty, image (opcional)
    session = Session()
    prod_id = data.get("id")
    if prod_id is None:
        session.close()
        return jsonify({"error": "ID do produto é obrigatório"}), 400
    existing = session.get(Product, prod_id)
    if existing:
        existing.name = data.get("name", existing.name)
        existing.description = data.get("description", existing.description)
        existing.price = float(data.get("price", existing.price))
        existing.stock_qty = int(data.get("stock_qty", existing.stock_qty))
        existing.image = data.get("image", existing.image)
        session.commit()
        session.close()
        return jsonify({"message": "Produto atualizado"}), 200
    else:
        newp = Product(
            id=int(prod_id),
            name=data.get("name", ""),
            description=data.get("description", ""),
            price=float(data.get("price", 0.0)),
            stock_qty=int(data.get("stock_qty", 0)),
            image=data.get("image", None)
        )
        session.add(newp)
        session.commit()
        session.close()
        return jsonify({"message": "Produto criado"}), 201

@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    session = Session()
    p = session.get(Product, product_id)
    if not p:
        session.close()
        return jsonify({"error": "Produto não encontrado"}), 404
    session.delete(p)
    session.commit()
    session.close()
    return jsonify({"message": "Produto excluído"}), 200

# upload de imagem simples
@app.route("/api/upload", methods=["POST"])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "arquivo não enviado"}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    return jsonify({"filename": filename}), 201

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# table carrinho
# adicionar item ao carrinho
@app.route("/api/cart/add", methods=["POST"])
def add_to_cart():
    data = request.json
    cart_id = data.get("cart_id") or str(uuid.uuid4())
    product_id = int(data["product_id"])
    qty = int(data.get("qty", 1))

    session = Session()
    product = session.get(Product, product_id)
    if not product:
        session.close()
        return jsonify({"error": "Produto não encontrado"}), 404
    if qty <= 0:
        session.close()
        return jsonify({"error": "Quantidade inválida"}), 400
    # inserir item no cart_items (não soma automaticamente)
    item = CartItem(
        cart_id=cart_id,
        product_id=product.id,
        product_name=product.name,
        unit_price=product.price,
        qty=qty,
        max_qty=product.stock_qty
    )
    session.add(item)
    session.commit()
    session.close()
    return jsonify({"message": "Item adicionado", "cart_id": cart_id}), 201

# listar itens do carrinho
@app.route("/api/cart/<string:cart_id>", methods=["GET"])
def get_cart(cart_id):
    session = Session()
    items = session.query(CartItem).filter_by(cart_id=cart_id).all()
    out = []
    total = 0.0
    for it in items:
        subtotal = it.unit_price * it.qty
        total += subtotal
        out.append({
            "id": it.id,
            "product_id": it.product_id,
            "product_name": it.product_name,
            "unit_price": it.unit_price,
            "qty": it.qty,
            "max_qty": it.max_qty,
            "subtotal": subtotal
        })
    session.close()
    return jsonify({"items": out, "total": total})

# remover item do carrinho
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

# fecha o pedido: calcula frete, desconta estoque pelos itens do carrinho e limpa o carrinho
@app.route("/api/cart/checkout", methods=["POST"])
def checkout():
    """
    Espera JSON:
    {
      "cart_id": "...",
      "shipping": "padrao" ou "expresso"
    }
    """
    data = request.json
    cart_id = data.get("cart_id")
    shipping = data.get("shipping", "padrao")  # default padrao

    # valores fixos de frete
    FRETES = {"padrao (10 dias úteis)": 10.0, "expresso (4 dias úteis)": 25.0}

    if shipping not in FRETES:
        return jsonify({"error": "Tipo de frete inválido"}), 400

    session = Session()
    items = session.query(CartItem).filter_by(cart_id=cart_id).all()
    if not items:
        session.close()
        return jsonify({"error": "Carrinho vazio"}), 400

    # calcular total e desconta estoque
    total_products = 0.0
    for it in items:
        total_products += it.unit_price * it.qty
        prod = session.get(Product, it.product_id)
        if not prod:
            session.close()
            return jsonify({"error": f"Produto {it.product_id} não existe"}), 400
        # verificar estoque se suficiente
        if it.qty > prod.stock_qty:
            session.close()
            return jsonify({"error": f"Estoque insuficiente para {prod.name}"}), 400
        prod.stock_qty -= it.qty

    frete_valor = FRETES[shipping]
    total_final = total_products + frete_valor

    # limpa o carrinho
    for it in items:
        session.delete(it)

    session.commit()
    session.close()
    return jsonify({"message": "Pedido finalizado", "total_products": total_products, "frete": frete_valor, "total": total_final}), 200

# teste servidor ON
@app.route('/')
def index():
    return jsonify({
        "message": "🚀 Servidor Flask do projeto_emeece está rodando com sucesso!",
        "endpoints": {
            "Listar produtos": "/api/products",
            "Carrinho": "/api/cart/<cart_id>",
            "Upload de imagem": "/api/upload"
        }
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
