from pyramid.view import view_config
from pyramid.response import Response
from sqlalchemy.exc import SQLAlchemyError
from pyramid.httpexceptions import HTTPFound,HTTPNotFound
from urllib3 import request
from shiva.models import MyModel, User, Product, RefreshToken
import base64
from sqlalchemy import or_
# shiva/views.py


from shiva.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password,
)
from datetime import datetime, timedelta



def get_current_user(request):
    token = request.cookies.get("token")

    if not token:
        return None

    try:
        payload = verify_token(token)
        user_id = payload.get("user_id")

        return request.dbsession.query(User).get(user_id)
    except:
        return None


@view_config(route_name='home')
def home_view(request):
    return HTTPFound(location=request.route_url('dashboard'))


@view_config(route_name='add_model', renderer='templates/model_form.jinja2')
def add_model(request):
   
    if request.method == 'POST':
        name = request.POST.get('name')
        value = request.POST.get('value')

        new_obj = MyModel(
            name=name,
            value=int(value)
        )

        request.dbsession.add(new_obj)
        
        return HTTPFound(location='/add_model')

    return {}





@view_config(route_name="signup", renderer="templates/signup.jinja2")
def signup_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Step 1: Check if both passwords match
        if password != confirm_password:
            return {
                "error": "Both passwords are not same. Please enter correct password."
            }

        # 🔎 Step 2: Check if user already exists
        existing_user = request.dbsession.query(User).filter(
            or_(
                User.username == username,
                User.email == email
            )
        ).first()

        if existing_user:
            return {
                "error": "Username or Email already exists"
            }

        # Step 3: Create user
        user = User(
            username=username,
            email=email,
            password=hash_password(password)
        )

        request.dbsession.add(user)

        return HTTPFound(location=request.route_url("login"))

    return {}



@view_config(route_name="login", renderer="templates/login.jinja2")
def login_view(request):

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = request.dbsession.query(User).filter(User.email == email).first()

        if user and verify_password(password, user.password):

            access_token = create_access_token({"user_id": user.id})
            refresh_token = create_refresh_token({"user_id": user.id})
            

            # Store refresh token in DB
            refresh_entry = RefreshToken(
                token=refresh_token,
                user_id=user.id,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            request.dbsession.add(refresh_entry)

            response = HTTPFound(location=request.route_url("dashboard"))
            response.set_cookie("token", access_token, httponly=True)
            response.set_cookie("refresh_token", refresh_token, httponly=True)

            return response

        return {"error": "Invalid email or password"}

    return {}


@view_config(route_name="refresh")
def refresh_view(request):

    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        return HTTPFound(location=request.route_url("login"))

    # Find token in DB
    stored_token = request.dbsession.query(RefreshToken).filter(
        RefreshToken.token == refresh_token,
        RefreshToken.is_revoked == False
    ).first()

    if not stored_token:
        return HTTPFound(location=request.route_url("login"))

    try:
        payload = verify_token(refresh_token)
        user_id = payload.get("user_id")

    except:
        return HTTPFound(location=request.route_url("login"))

    # 🔥 ROTATION STARTS HERE

    # 1️⃣ Revoke old token
    stored_token.is_revoked = True

    # 2️⃣ Issue new tokens
    new_access = create_access_token({"user_id": user_id})
    new_refresh = create_refresh_token({"user_id": user_id})

    # 3️⃣ Store new refresh token
    new_entry = RefreshToken(
        token=new_refresh,
        user_id=user_id,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )

    request.dbsession.add(new_entry)

    response = HTTPFound(location=request.route_url("dashboard"))
    response.set_cookie("token", new_access, httponly=True)
    response.set_cookie("refresh_token", new_refresh, httponly=True)

    return response



@view_config(route_name="dashboard", renderer="templates/dashboard.jinja2")
def dashboard_view(request):
    return {}


@view_config(route_name='profile', renderer='templates/profile.jinja2')
def profile_view(request):

    user = get_current_user(request)

    if not user:
        return HTTPFound(location=request.route_url('login'))

    return {
        'user': user
    }

@view_config(route_name="logout")
def logout_view(request):

    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        stored_token = request.dbsession.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False
        ).first()

        if stored_token:
            stored_token.is_revoked = True  # ✅ Mark revoked

    response = HTTPFound(location="/login")
    response.delete_cookie("token")
    response.delete_cookie("refresh_token")

    return response



@view_config(route_name='product_form', renderer='templates/product_form.jinja2')
def product_form(request):
    

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = float(request.POST.get('price'))

  
       
        image_file = request.POST.get('image')
        if hasattr(image_file, 'file') and image_file.filename:
            image_bytes = image_file.file.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

       
        
        current_user = get_current_user(request)

        if not current_user:
            return HTTPFound(location=request.route_url("login"))

        new_obj = Product(
            name=name,
            description=description,
            price=price,
            image=image_base64,
            user_id=current_user.id   #  Attach product to logged-in user
        )
        request.dbsession.add(new_obj)

       
      
        return HTTPFound(location=request.route_url('product_list'))
        
    return {
        "message": "Product added successfully!"
    }   


@view_config(route_name="product_list", renderer="templates/product_list.jinja2")
def product_list(request):
 
    # products = session.query(m.Product).all()
    current_user = get_current_user(request)

    if not current_user:
        return HTTPFound(location=request.route_url("login"))

    products = (
        request.dbsession.query(Product)
        .filter(
            Product.user_id == current_user.id,
            Product.is_deleted == False
        )
        .all()
    )
    return {
        "products": products
    }




@view_config(
    route_name='product_update',
    renderer='templates/product_update.jinja2'
)
def product_update(request):
  
    product_id = request.matchdict.get('id')

    product = request.dbsession.query(Product).get(product_id)

    if not product:
        raise HTTPNotFound("Product not found")

    current_user = get_current_user(request)

    if not current_user or product.user_id != current_user.id:
        raise HTTPNotFound("Not allowed")

    # 🔹 UPDATE (POST)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = float(request.POST.get('price'))

        image_file = request.POST.get('image')

        if image_file is not None and getattr(image_file, "filename", ""):
            image_bytes = image_file.file.read()
            product.image = base64.b64encode(image_bytes).decode("utf-8")

        return HTTPFound(location=request.route_url('product_list'))

    # 🔹 EDIT PAGE (GET)
    return {
        'product': product
    }
    

@view_config(route_name='product_delete', request_method='POST')
def product_delete(request):
    
    product_id = request.matchdict.get('id')

    product = request.dbsession.query(Product).get(product_id)

    if not product:
        raise HTTPNotFound("Product not found")

    current_user = get_current_user(request)

    if not current_user or product.user_id != current_user.id:
        raise HTTPNotFound("Not allowed")

    request.dbsession.delete(product)
   
    
    return HTTPFound(location=request.route_url('product_list'))




@view_config(route_name='product_soft_delete', request_method='POST')
def product_soft_delete(request):
    
    product_id = request.matchdict.get('id')

    product = request.dbsession.query(Product).get(product_id)

    if not product:
        raise HTTPNotFound("Product not found")
    
    current_user = get_current_user(request)

    if not current_user or product.user_id != current_user.id:
        raise HTTPNotFound("Not allowed")


    product.is_deleted = True   # 👈 Soft delete instead of real delete
    

    return HTTPFound(location=request.route_url('product_list'))
