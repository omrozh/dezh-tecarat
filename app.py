import flask
from flask_sqlalchemy import SQLAlchemy
from uuid import uuid4
import constants
from sqlalchemy import distinct, or_, case, asc, func, literal_column, union
from sqlalchemy.event import listen
import Levenshtein

app = flask.Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SECRET_KEY"] = "jsiv-3mdxa-svFS3-afsaSW"

db = SQLAlchemy(app=app)


def python_unicode_lower(text_from_db):
    if text_from_db is None:
        return None
    return str(text_from_db).lower()


def python_levenshtein_distance(s1, s2):
    if s1 is None or s2 is None:
        return 999
    return Levenshtein.distance(str(s1), str(s2))


def _setup_custom_sqlite_functions(dbapi_con, connection_record):
    dbapi_con.create_function("unicode_lower", 1, python_unicode_lower)
    dbapi_con.create_function("levenshtein", 2, python_levenshtein_distance)


with app.app_context():
    if app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("sqlite"):
        if db.engine is not None:
            listen(db.engine, "connect", _setup_custom_sqlite_functions)


class User(db.Model):
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)

    @property
    def orders(self):
        return Order.query.filter_by(user_fk=self.id).all()

    @property
    def addresses(self):
        return Address.query.filter_by(user_fk=self.id)

    @property
    def wishlist(self):
        return WishlistedItem.query.filter_by(user_fk=self.id).all()

    @property
    def ratings(self):
        return ProductRating.query.filter_by(user_fk=self.id).all()

    @property
    def tickets(self):
        return ProductSupportTicket.query.filter_by(user_fk=self.id).all()


class Product(db.Model):
    id = db.Column(db.String, primary_key=True)
    brand_name = db.Column(db.String)
    product_name = db.Column(db.String)
    product_description = db.Column(db.Text)
    product_price_in_liras = db.Column(db.Float)
    product_is_active = db.Column(db.Boolean, default=True)

    @property
    def images(self):
        return ProductImage.query.filter_by(product_fk=self.id).all()

    @property
    def variation_types(self):
        return ProductVariationType.query.filter_by(product_fk=self.id).all()

    @property
    def shortened_name(self):
        if not self.brand_name or not self.product_name:
            return self.product_name or self.brand_name or ""
        brand_name_length = len(self.brand_name.split(" "))
        additional_piece_words = self.product_name.split(" ")[:max(1, 7 - brand_name_length)]
        additional_piece = " ".join(additional_piece_words)
        if len(self.product_name.split(" ")) > len(additional_piece_words):
            additional_piece += "..."
        return additional_piece

    @property
    def categories(self):
        return ProductCategory.query.filter_by(product_fk=self.id).all()


class ProductImage(db.Model):
    id = db.Column(db.String, primary_key=True)
    image_uri = db.Column(db.String)
    product_fk = db.Column(db.String)


class ProductVariationType(db.Model):
    id = db.Column(db.String, primary_key=True)
    variation_type = db.Column(db.String)
    product_fk = db.Column(db.String)

    @property
    def variations(self):
        return ProductVariation.query.filter_by(product_variation_type_fk=self.id).all()


class ProductVariation(db.Model):
    id = db.Column(db.String, primary_key=True)
    variation_value = db.Column(db.String)
    product_variation_type_fk = db.Column(db.String)


class ProductCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_fk = db.Column(db.String)
    product_fk = db.Column(db.String)
    product_is_boosted = db.Column(db.Boolean)

    @property
    def product(self):
        return Product.query.get(self.product_fk)

    @property
    def category(self):
        return Category.query.get(self.category_fk)


class Category(db.Model):
    id = db.Column(db.String, primary_key=True)
    category_name = db.Column(db.String)

    @property
    def all_products(self):
        product_fks = [pc.product_fk for pc in ProductCategory.query.filter_by(category_fk=self.id).all()]
        if not product_fks:
            return []
        return Product.query.filter(Product.id.in_(product_fks)).filter_by(product_is_active=True).all()

    @property
    def boosted_products(self):
        product_fks = [pc.product_fk for pc in ProductCategory.query.filter_by(
            category_fk=self.id).filter_by(product_is_boosted=True).all()]
        if not product_fks:
            return []
        return Product.query.filter(Product.id.in_(product_fks)).filter_by(product_is_active=True).all()


class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String)
    address_name = db.Column(db.String)
    user_fk = db.Column(db.String)


class Order(db.Model):
    id = db.Column(db.String, primary_key=True)
    user_fk = db.Column(db.String)
    order_price = db.Column(db.Float)
    product_fk = db.Column(db.String)
    order_date = db.Column(db.Date)
    order_status = db.Column(db.String, default=constants.ORDER_PLACED if 'constants' in globals() else "ORDER_PLACED")
    order_tracking_link = db.Column(db.String,
                                    default=constants.TRACKING_STATUS_NOT_PRESENT if 'constants' in globals() else "TRACKING_NOT_AVAILABLE")
    address_fk = db.Column(db.Integer)

    @property
    def product(self):
        return Product.query.get(self.product_fk)

    @property
    def user(self):
        return User.query.get(self.user_fk)


class WishlistedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_fk = db.Column(db.String)
    user_fk = db.Column(db.String)


class ProductRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_fk = db.Column(db.String)
    user_fk = db.Column(db.String)
    rating_score = db.Column(db.Integer)
    rating_comment = db.Column(db.String)


class ProductSupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_fk = db.Column(db.String)
    support_request = db.Column(db.String)
    support_status = db.Column(db.String,
                               default=constants.SUPPORT_REQUEST_RECEIVED if 'constants' in globals() else "REQUEST_RECEIVED")

    @property
    def order(self):
        return Order.query.get(self.order_fk)


def autocomplete(query: str):
    if not query or not query.strip():
        return []

    search_term = f"{python_unicode_lower(query.strip())}%"

    brand_q = db.session.query(Product.brand_name.label("suggestion")).distinct() \
        .filter(Product.brand_name.isnot(None)) \
        .filter(func.unicode_lower(Product.brand_name).like(search_term))

    category_q = db.session.query(Category.category_name.label("suggestion")).distinct() \
        .filter(Category.category_name.isnot(None)) \
        .filter(func.unicode_lower(Category.category_name).like(search_term))

    product_name_q = db.session.query(Product.product_name.label("suggestion")).distinct() \
        .filter(Product.product_name.isnot(None)) \
        .filter(func.unicode_lower(Product.product_name).like(search_term))

    combined_query = brand_q.union(category_q, product_name_q)

    results = combined_query.limit(10).all()

    suggestions = [item[0] for item in results]

    return list(set(suggestions))


def search_products_by_name_or_brand(query_term: str):
    query_term_lower_full = ""
    if query_term and query_term.strip():
        query_term_lower_full = python_unicode_lower(query_term.strip())

    lev_dist_name = func.levenshtein(func.unicode_lower(Product.product_name), query_term_lower_full).label(
        "lev_dist_name")
    lev_dist_brand = func.levenshtein(func.unicode_lower(Product.brand_name), query_term_lower_full).label(
        "lev_dist_brand")

    query_words = []
    if query_term_lower_full:
        query_words = [word for word in query_term_lower_full.split() if word]

    num_matched_substring_words_expr = literal_column("0")
    if query_words:
        current_sum_expr = literal_column("0")
        for word in query_words:
            word_pattern = f"%{word}%"
            is_word_substring_expr = case(
                (or_(
                    func.unicode_lower(Product.product_name).like(word_pattern),
                    func.unicode_lower(Product.brand_name).like(word_pattern)
                ), 1),
                else_=0
            )
            current_sum_expr = current_sum_expr + is_word_substring_expr
        num_matched_substring_words_expr = current_sum_expr

    num_matched_substring_words_labelled = num_matched_substring_words_expr.label("num_matched_substring_words")

    pn_exact_match = literal_column("0")
    pn_starts_with_match = literal_column("0")
    pn_contains_match = literal_column("0")
    bn_exact_match = literal_column("0")
    bn_starts_with_match = literal_column("0")
    bn_contains_match = literal_column("0")

    if query_term_lower_full:
        pn_exact_match = (func.unicode_lower(Product.product_name) == query_term_lower_full)
        pn_starts_with_match = func.unicode_lower(Product.product_name).like(f"{query_term_lower_full}%")
        pn_contains_match = func.unicode_lower(Product.product_name).like(f"%{query_term_lower_full}%")

        bn_exact_match = (func.unicode_lower(Product.brand_name) == query_term_lower_full)
        bn_starts_with_match = func.unicode_lower(Product.brand_name).like(f"{query_term_lower_full}%")
        bn_contains_match = func.unicode_lower(Product.brand_name).like(f"%{query_term_lower_full}%")

    product_name_full_phrase_match_quality = case(
        (pn_exact_match, 1),
        (pn_starts_with_match, 2),
        (pn_contains_match, 3),
        else_=4
    ).label("pn_full_phrase_match_quality")

    brand_name_full_phrase_match_quality = case(
        (bn_exact_match, 1),
        (bn_starts_with_match, 2),
        (bn_contains_match, 3),
        else_=4
    ).label("bn_full_phrase_match_quality")

    original_primary_ranking_logic = case(
        (pn_contains_match & bn_contains_match, 1),
        (pn_contains_match, 2),
        (bn_contains_match, 3),
        else_=4
    ).label("original_primary_rank")

    products_query = Product.query.add_columns(
        lev_dist_name,
        lev_dist_brand,
        num_matched_substring_words_labelled,
        original_primary_ranking_logic,
        product_name_full_phrase_match_quality,
        brand_name_full_phrase_match_quality
    ).filter(
        Product.product_is_active == True
    ).order_by(
        product_name_full_phrase_match_quality.asc(),
        brand_name_full_phrase_match_quality.asc(),

        num_matched_substring_words_labelled.desc(),

        lev_dist_name.asc(),
        lev_dist_brand.asc(),

        original_primary_ranking_logic.asc(),

        asc(func.length(Product.product_name)),
        asc(func.length(Product.brand_name)),
        Product.product_name.asc()
    )
    results = products_query.all()

    products_found = [result_tuple[0] for result_tuple in results]

    return products_found


def remove_category(category_id):
    db.session.delete(Category.query.get(category_id))
    for i in ProductCategory.query.filter_by(category_fk=category_id).all():
        db.session.delete(i)
    db.session.commit()


def get_all_sizes_for_category(category):
    query = db.session.query(distinct(ProductVariation.variation_value)) \
        .join(ProductVariationType, ProductVariation.product_variation_type_fk == ProductVariationType.id) \
        .join(Product, ProductVariationType.product_fk == Product.id) \
        .join(ProductCategory, Product.id == ProductCategory.product_fk) \
        .join(Category, ProductCategory.category_fk == Category.id) \
        .filter(Category.category_name == category) \
        .filter(
        ProductVariationType.variation_type == (constants.SIZE_VARIATION_TYPE if 'constants' in globals() else "SIZE")) \
        .filter(ProductVariation.variation_value.isnot(None)) \
        .filter(ProductVariation.variation_value != '')
    raw_results = query.all()

    all_size_options = sorted([item[0] for item in raw_results if item[0] and item[0].strip()])

    return all_size_options


def get_all_brands_for_category(category):
    query = db.session.query(Product.brand_name).distinct() \
        .join(ProductCategory, ProductCategory.product_fk == Product.id) \
        .join(Category, ProductCategory.category_fk == Category.id) \
        .filter(Category.category_name == category) \
        .filter(Product.brand_name.isnot(None))

    raw_results = query.all()

    all_brand_options = sorted(
        list(set(item[0] for item in raw_results if item[0] is not None and item[0].strip() != "")))
    return all_brand_options


def get_all_products_in_category_by_brand(category_name, brand_name):
    query = db.session.query(Product).distinct() \
        .join(ProductCategory, Product.id == ProductCategory.product_fk) \
        .join(Category, ProductCategory.category_fk == Category.id) \
        .filter(Category.category_name == category_name) \
        .filter(Product.brand_name == brand_name) \
        .filter(Product.product_is_active == True)

    return query.all()


def get_all_products_in_category_by_size(category_name, size_value):
    query = db.session.query(Product).distinct() \
        .join(ProductCategory, Product.id == ProductCategory.product_fk) \
        .join(Category, ProductCategory.category_fk == Category.id) \
        .join(ProductVariationType, Product.id == ProductVariationType.product_fk) \
        .join(ProductVariation, ProductVariationType.id == ProductVariation.product_variation_type_fk) \
        .filter(Category.category_name == category_name) \
        .filter(
        ProductVariationType.variation_type == (constants.SIZE_VARIATION_TYPE if 'constants' in globals() else "SIZE")) \
        .filter(ProductVariation.variation_value == size_value) \
        .filter(Product.product_is_active == True)

    return query.all()


def get_all_sizes():
    query = db.session.query(distinct(ProductVariation.variation_value)) \
        .join(ProductVariationType, ProductVariation.product_variation_type_fk == ProductVariationType.id) \
        .filter(
        ProductVariationType.variation_type == (constants.SIZE_VARIATION_TYPE if 'constants' in globals() else "SIZE")) \
        .filter(ProductVariation.variation_value.isnot(None)) \
        .filter(ProductVariation.variation_value != '')

    raw_results = query.all()

    all_size_options = sorted([item[0] for item in raw_results if item[0] and item[0].strip()])

    return all_size_options


def get_all_brands():
    query = db.session.query(Product.brand_name).distinct() \
        .filter(Product.brand_name.isnot(None)) \
        .filter(Product.brand_name != '')

    raw_results = query.all()

    all_brand_options = sorted(
        list(set(item[0] for item in raw_results if item[0] is not None and item[0].strip() != "")))

    return all_brand_options


@app.route("/")
def index():
    return flask.render_template("index.html")


@app.route("/admin/product")
def admin_product():
    return flask.render_template(
        "admin/product/main.html",
        products=Product.query.all(),
        categories=Category.query.all()
    )


@app.route("/admin/update_item_status/<item_id>")
def admin_update_item_status(item_id):
    Product.query.get(item_id).product_is_active = not Product.query.get(item_id).product_is_active
    db.session.commit()
    return flask.redirect("/admin/product")


@app.route("/admin/category/add", methods=["POST", "GET"])
def admin_category_add():
    if flask.request.method == "POST":
        values = flask.request.values
        new_category = Category(id=str(uuid4()), category_name=values.get("category_name"))
        db.session.add(new_category)
        db.session.commit()
        return flask.redirect("/admin/product")
    return flask.render_template("admin/categories/add.html")


@app.route("/admin/remove/category/<category_id>")
def admin_remove_category(category_id):
    remove_category(category_id)
    return flask.redirect("/admin/product")


@app.route("/admin/product/add", methods=["POST", "GET"])
def admin_product_add():
    if flask.request.method == "POST":
        values = flask.request.values
        new_product = Product(
            id=str(uuid4()),
            brand_name=values["brand_name"],
            product_name=values["product_name"],
            product_description=values["product_description"],
            product_price_in_liras=float(values["product_price_in_liras"])
        )

        for i in values.keys():
            if "variation_type" in i:
                new_variation_type = ProductVariationType(
                    id=str(uuid4()),
                    variation_type=values[i],
                    product_fk=new_product.id
                )
                db.session.add(new_variation_type)
                for c in values[i.replace("variation_type_", "variation_values_")].split(","):
                    new_variation = ProductVariation(
                        id=str(uuid4()),
                        variation_value=c,
                        product_variation_type_fk=new_variation_type.id
                    )
                    db.session.add(new_variation)
        for i in flask.request.files.keys():
            file_id = str(uuid4())
            flask.request.files.get(i).save(f"static/{file_id}")
            new_product_image = ProductImage(id=str(uuid4()), image_uri=f"/static/{file_id}", product_fk=new_product.id)
            db.session.add(new_product_image)

        for i in values.get("categories").split(","):
            if len(i) > 1:
                category = Category.query.filter_by(category_name=i).first()
                new_product_category = ProductCategory(
                    category_fk=category.id,
                    product_fk=new_product.id,
                    product_is_boosted=False
                )
                db.session.add(new_product_category)

        db.session.add(new_product)
        db.session.commit()

        return flask.redirect("/admin/product/add")
    return flask.render_template("admin/product/add.html")


@app.route("/styles/<filename>")
def styles(filename):
    return flask.send_file(f"styles/{filename}")


@app.route("/static/<filename>")
def static_host(filename):
    return flask.send_file(f"static/{filename}")


@app.route("/pdp/<product_id>")
def product_detail_page(product_id):
    return flask.render_template("pdp.html")


@app.route("/profile")
def profile():
    return flask.render_template("profile.html")


@app.route("/scripts/<filename>")
def scripts(filename):
    return flask.send_file("scripts/" + filename)


@app.route("/feed")
def feed():
    query_term = flask.request.args.get("q", constants.SKIP_SEARCH)
    products = []

    brands = get_all_brands()
    sizes = get_all_sizes()
    category_pick = None

    if query_term == constants.SKIP_SEARCH:
        category_pick = flask.request.args.get("cat", constants.SKIP_CATEGORY)
        if category_pick == constants.SKIP_CATEGORY:
            products = Product.query.all()
        else:
            brands = get_all_brands_for_category(category=category_pick)
            sizes = get_all_sizes_for_category(category=category_pick)

            products = Category.query.filter_by(category_name=category_pick).first().all_products
    else:
        category_with_term = Category.query.filter_by(category_name=query_term).first()
        if category_with_term:
            products = category_with_term.all_products
            brands = get_all_brands_for_category(category=category_with_term.category_name)
            sizes = get_all_sizes_for_category(category=category_with_term.category_name)
        else:
            if query_term in get_all_brands():
                products = Product.query.filter_by(brand_name=query_term).all()
            else:
                products = search_products_by_name_or_brand(query_term)

    fe_query_term = category_pick if category_pick and not category_pick == constants.SKIP_CATEGORY \
        else "Ürün, kategori veya marka ara" if query_term == constants.SKIP_SEARCH else query_term

    return flask.render_template(
        "product-feed.html",
        products=products,
        brands=brands,
        sizes=sizes,
        fe_query=fe_query_term
    )


@app.route("/review", methods=["POST", "GET"])
def review_order():
    order = Order.query.get(flask.request.args.get("order"))
    values = flask.request.json

    new_product_rating = ProductRating(
        product_fk=order.product_fk,
        user_fk=order.user_fk,
        rating_score=int(values.get("rating")),
        rating_comment=values.get("comment")
    )
    db.session.add(new_product_rating)
    db.session.commit()

    return "OK"


@app.route("/autocomplete")
def autocomplete_resp():
    return flask.jsonify(autocomplete(flask.request.args.get("q")))


# TO DO: Make sure every order listed in profile has order id as their id as a HTML element
