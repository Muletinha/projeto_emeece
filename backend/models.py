from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    # ID sem autoincremento (você já usa o ID escolhido no admin)
    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    stock_qty = Column(Integer, nullable=False, default=0)
    image = Column(String(255), nullable=True)

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(String(64), nullable=False)  # identifica o carrinho do usuário
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(255), nullable=False)
    unit_price = Column(Float, nullable=False)
    qty = Column(Integer, nullable=False)
    # max_qty = snapshot do estoque no momento do add (para UX)
    max_qty = Column(Integer, nullable=False)
    product = relationship("Product", foreign_keys=[product_id])

def get_engine_and_session(db_user="root", db_pass="", db_host="localhost", db_name="projeto_emeece"):
    url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
    engine = create_engine(url, future=True)
    Session = sessionmaker(bind=engine, future=True)
    return engine, Session
