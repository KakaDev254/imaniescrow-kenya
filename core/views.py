from django.shortcuts import render
from django.contrib import messages

def home(request):
    context = {
        'trusted_by': '10,000+ Kenyans',
        'total_escrowed': 'KES 500M+',
        'successful_transactions': '15,000+',
    }
    return render(request, 'core/home.html', context)

def how_it_works(request):
    return render(request, 'core/how_it_works.html')

def pricing(request):
    return render(request, 'core/pricing.html')

def about(request):
    return render(request, 'core/about.html')

def contact(request):
    if request.method == 'POST':
        # Handle contact form
        messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
    return render(request, 'core/contact.html')