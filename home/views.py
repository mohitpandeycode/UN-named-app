from django.shortcuts import render,redirect,get_object_or_404
from .models import *
from django.contrib.auth import authenticate, login, logout  
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User  
from django.contrib import messages, auth
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q


# Create your views here.


# home page of the website
def index(request):
    # Check if there are search parameters
    if 'address' in request.GET or 'prod' in request.GET:
        search_results = search_products(request)  # call search function
        if search_results.exists():  # Render search results only if they exist
            return render(request, "allProducts.html", {'products': search_results})
        else:
            return render(request, "allProducts.html")
    
    # Default behavior for the index page
    products = Product.objects.order_by('?')[:16]
    for product in products:
        # Fetch the associated images for each product
        product.images = ProductImages.objects.filter(product=product)
    categories = Category.objects.order_by('?')[:5]

    # Handle user authentication (if required)
    auth_response = handle_user_auth(request)  # call authentication function
    if auth_response:
        return auth_response  # Redirect if authentication actions occurred

    # Render the index page
    context = {'products': products, 'categories': categories}
    return render(request, 'index.html', context)



# login signup auth function for the website
def handle_user_auth(request):
    if request.method == "POST":
        # Determine the type of form submitted (signup or login)
        form_type = request.POST.get("form_type")
        
        if form_type == "signup":
            # Handle signup form submission
            first_name = request.POST.get('fname')  # Get first name from form
            last_name = request.POST.get('lname')  # Get last name from form
            username = request.POST.get('username')  # Get username from form
            email = request.POST.get('email')  # Get email from form
            phone = request.POST.get('phone')  # Get phone number from form
            password = request.POST.get('password')  # Get password from form
            cpassword = request.POST.get('cpassword')  # Get confirm password from form
            
            # Check if passwords match
            if password != cpassword:
                messages.error(request, "Passwords do not match.")  # Show error message
                return redirect(request.path)  # Redirect back to the same page

            # Check if the username already exists
            if CustomUser.objects.filter(username=username).exists():
                messages.warning(request, "Username already taken. Sign in again!!!")  # Show error message
                return redirect(request.path)  # Redirect back to the same page
            if CustomUser.objects.filter(phone_number=phone).exists():
                messages.warning(request, "User form this number is already signed in.")  # Show error message
                return redirect(request.path)  # Redirect back to the same page

            # Create a new user if validation passes
            user = CustomUser.objects.create_user(username, email, password)
            user.first_name = first_name  # Set first name
            user.last_name = last_name  # Set last name
            user.phone_number = phone  # Set phone number
            user.save()  # Save the user
            messages.success(request, "Account created successfully.")  # Show success message
            return redirect(request.path)  # Redirect back to the same page

        elif form_type == "login":
            # Handle login form submission
            username = request.POST.get('lusername')  # Get username from form
            password = request.POST.get('lpassword')  # Get password from form
            
            # Check if the username exists
            if not CustomUser.objects.filter(username=username).exists():
                messages.error(request, 'Invalid Username!')  # Show error message
                return redirect(request.path)  # Redirect back to the same page

            # Authenticate the user
            user = auth.authenticate(request, username=username, password=password)
            if user is None:
                messages.error(request, 'Invalid Password!')  # Show error message
                return redirect(request.path)  # Redirect back to the same page
            
            # Log the user in
            auth.login(request, user)
            messages.success(request, "Logged in successfully.")  # Show success message
            return redirect(request.path)  # Redirect back to the same page



# logout function for the website
@login_required
def handle_logout(request):
    logout(request)
    messages.success(request, "You're logged out")
    return redirect("/")



# function for all products page
def allproducts(request):
    if 'address' in request.GET or 'prod' in request.GET:
        search_results = search_products(request)
        if search_results.exists():  # Render search results only if they exist
            return render(request, "allProducts.html", {'products': search_results})
        else:
            return render(request, "allProducts.html")
        
    products = Product.objects.all()  # Fetch all products
    for product in products:
        # Fetch the associated images for each product
        product.images = ProductImages.objects.filter(product=product)
    
    context = {'products': products}

    # check login signup in this page also by using auth function
    auth_response = handle_user_auth(request)
    if auth_response:
        return auth_response  # Redirect if authentication actions occurred
    return render(request, 'allProducts.html', context)



#function for selling items form
def sellItem(request):
    auth_response = handle_user_auth(request)
    if auth_response:
        return auth_response  # Redirect if authentication actions occurred

    condition_choices = Product.condition_choices
    category = Category.objects.all()

    if request.method == "POST":
        cate_name = request.POST.get('category')  # Get the category name from the form
        category_instance = Category.objects.filter(name=cate_name).first()  # Get the Category instance

        # Handle other form fields
        brand = request.POST.get('brand')
        title = request.POST.get('title')
        description = request.POST.get('description')
        condition = request.POST.get('condition')
        price = request.POST.get('price')
        location = request.POST.get('location')
        image1 = request.FILES.get('img1')
        image2 = request.FILES.get('img2')
        image3 = request.FILES.get('img3')
        image4 = request.FILES.get('img4')

        # Check if the category instance exists
        if category_instance:
            product = Product.objects.create(
                category=category_instance,  # Assign the Category instance
                brand=brand,
                title=title,
                description=description,
                price=price,
                location=location,
                condition=condition,
                seller=request.user
            )

            # Create ProductImages
            ProductImages.objects.create(
                product=product,
                image1=image1,
                image2=image2,
                image3=image3,
                image4=image4,
                user=request.user
            )

            messages.success(request, "Product added successfully.")
            return redirect('/allproducts/')
        else:
            messages.error(request, "Category not found.")
            return redirect('sell_item')  # Redirect back to the form

    context = {'condition_choices': condition_choices, 'categories': category}
    return render(request, 'sellitem.html', context)



#function for searching products
def search_products(request):
    # Get the address and product search parameters
    address = request.GET.get('address')
    product = request.GET.get('prod')

    # Start with all products
    products = Product.objects.all()

    # Apply address filter if provided
    if address:
        products = products.filter(location__icontains=address)

    # Apply product filter if provided
    if product:
        products = products.filter(
            Q(brand__icontains=product) |
            Q(title__icontains=product) |
            Q(description__icontains=product) |
            Q(category__name__icontains=product)  # Access category name
        )

    # Attach images to each product
    for prod in products:
        prod.images = ProductImages.objects.filter(product=prod)

    return products


#product by category function
def prodbyCategory(request, category):
    # Check if there are search parameters
    if 'address' in request.GET or 'prod' in request.GET:
        search_results = search_products(request)
        if search_results.exists():  # Render search results only if they exist
            return render(request, "allProducts.html", {'products': search_results})
        else:
            return render(request, "allProducts.html")
    products = Product.objects.filter(category__name=category)  # Fetch products by category
    for product in products:
        # Fetch the associated images for each product
        product.images = ProductImages.objects.filter(product=product)
    context = {'products': products}

    return render(request, 'allProducts.html', context)


# product details function
def view_Product(request, slug):
    if 'address' in request.GET or 'prod' in request.GET:
        search_results = search_products(request)  # call search function
        if search_results.exists():  # Render search results only if they exist
            return render(request, "allProducts.html", {'products': search_results})
        else:
            return render(request, "allProducts.html")
      # Handle user authentication (if required)
    auth_response = handle_user_auth(request)  # call authentication function
    if auth_response:
        return auth_response  # Redirect if authentication actions occurred

        
    product = Product.objects.get(slug=slug)
    product.views += 1
    product.save()
    product.images = ProductImages.objects.filter(product=product)
    context = {'product': product}
    return render(request, 'viewProduct.html', context)


# Report for a add 
@login_required
def reportad(request, slug):
    product = get_object_or_404(Product, slug=slug)

    if request.method == "POST":
        reason = request.POST.get("reason")
        description = request.POST.get("description", "").strip()

        if not reason:
            messages.error(request, "Please select a reason")
            return redirect('viewproduct',slug=slug)

        Repoerted_ad.objects.create(
            product=product,
            reporter=request.user,
            reason=reason,
            description=description[:500]  # Limit to 500 characters
        )

        messages.success(request, "Your report has been submitted successfully.")
        return redirect('viewproduct', slug=slug)
    context = {'product': product}
    return render(request, 'viewProduct.html', context)


#profile page function
@login_required
def profilePage(request):
    if 'address' in request.GET or 'prod' in request.GET:
        search_results = search_products(request)  # call search function
        if search_results.exists():  # Render search results only if they exist
            return render(request, "allProducts.html", {'products': search_results})
        else:
            return render(request, "allProducts.html")
      # Handle user authentication (if required)
    auth_response = handle_user_auth(request)  # call authentication function
    if auth_response:
        return auth_response  # Redirect if authentication actions occurred

    product_ads = Product.objects.filter(seller=request.user)
    for product in product_ads:
        # Fetch the associated images for each product
        product.images = ProductImages.objects.filter(product=product)
    context = {'products': product_ads}
    return render(request, 'profilePage.html',context)


#ads page function
@login_required
def adsPage(request):
    if 'address' in request.GET or 'prod' in request.GET:
        search_results = search_products(request)  # call search function
        if search_results.exists():  # Render search results only if they exist
            return render(request, "allProducts.html", {'products': search_results})
        else:
            return render(request, "allProducts.html")
      # Handle user authentication (if required)
    auth_response = handle_user_auth(request)  # call authentication function
    if auth_response:
        return auth_response  # Redirect if authentication actions occurred

    product_ads = Product.objects.filter(seller=request.user)
    for product in product_ads:
        # Fetch the associated images for each product
        product.images = ProductImages.objects.filter(product=product)
    context = {'products': product_ads}
    return render(request, 'adsPage.html',context)


#delete ad function
@login_required
def deleteAd(request, slug):
    product = Product.objects.get(slug=slug)
    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect('adspage') 


#settings page function
@login_required
def settingsPage(request):
    if 'address' in request.GET or 'prod' in request.GET:
        search_results = search_products(request)  # call search function
        if search_results.exists():  # Render search results only if they exist
            return render(request, "allProducts.html", {'products': search_results})
        else:
            return render(request, "allProducts.html")
        
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        
        if form_type == "changepass":
            newpass = request.POST.get('newpass')
            cpass = request.POST.get('cpass')
            if newpass != cpass:
                messages.error(request, "Passwords do not match.")
                return redirect('settings')
            
            elif request.user.check_password(newpass):
                messages.error(request, "password is same as old password.")
                return redirect('settings')
            else:
                user = request.user  # Directly use the logged-in user
                user.set_password(newpass)
                user.save()
                update_session_auth_hash(request, user)  # Keep the user logged in
                messages.success(request, "Password changed successfully.")
                return redirect('settings')
            
        elif form_type == "personaldetails":
            fName = request.POST.get('fname')
            lName = request.POST.get('lname')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            email = request.POST.get('email')
            user = request.user  # Get the currently logged-in user
        
        # Update user fields
            user.first_name = fName
            user.last_name = lName
            user.phone_number = phone
            user.email = email
            user.address = address
            user.save()  # Save changes
        
            messages.success(request, "Your details have been updated successfully!")
            return redirect('settings')
        
    return render(request, 'settings.html')


#delete account function
@login_required
def deleteAccount(request):
    user = request.user
    user.delete()
    messages.success(request, "Account deleted successfully.")
    return redirect('/')


#product seller profile
def viewSeller(request, slug):
    if 'address' in request.GET or 'prod' in request.GET:
        search_results = search_products(request)  # call search function
        if search_results.exists():  # Render search results only if they exist
            return render(request, "allProducts.html", {'products': search_results})
        else:
            return render(request, "allProducts.html")
      # Handle user authentication (if required)
    auth_response = handle_user_auth(request)  # call authentication function
    if auth_response:
        return auth_response  # Redirect if authentication actions occurred
    seller = CustomUser.objects.get(username = slug)
    products = Product.objects.filter(seller=seller)
    for product in products:
        # Fetch the associated images for each product
        product.images = ProductImages.objects.filter(product=product)
    context = {'seller': seller,'products':products}
    return render(request, 'sellerprofile.html',context)















