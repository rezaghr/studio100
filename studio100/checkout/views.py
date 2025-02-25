import requests
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect
from checkout.models import invoices
from admin_panel.models import user_data, price
import os

def payment_request(request, id):
    website = os.getenv("WEBSITE_URL")
    merchent = os.getenv("ZARINPAL_MERCHANT_ID")
    try:
        # Fetch the invoice by order_id and update status
        invoice = invoices.objects.get(id=id)
        amount = invoice.amount
    except invoices.DoesNotExist:
        return HttpResponse("invoice not found")
    url = 'https://payment.zarinpal.com/pg/v4/payment/request.json'  # Updated URL
    start_pay_url = 'https://payment.zarinpal.com/pg/StartPay/'  # Corrected URL for StartPay

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    data = {
        "merchant_id": merchent,
        "amount": amount,  # Ensure this matches exactly
        "callback_url": f"{website}/checkout/verify/{id}/",
        "description": "purchase for token, artech bot",
        "metadata": {
            "order_id": id
        }
    }
    
    # Make the POST request
    response = requests.post(url, json=data, headers=headers)
    # Check if response is valid and handle errors
    try:
        response_data = response.json()
        if 'data' in response_data and 'authority' in response_data['data']:
            authority = response_data['data']["authority"]
            redirect_url = f"{start_pay_url}{authority}"
            return redirect(redirect_url)
        else:
            # Log the error details and return a message
            error_message = response_data.get('errors', 'Unexpected response format from Zarinpal')
            return HttpResponse(f"Payment request failed: {error_message}", status=500)
    except (ValueError, KeyError) as e:
        # Handle JSON decoding errors or missing fields
        return HttpResponse(f"Failed to process payment request: {str(e)}", status=500)

def payment_verify(request, invoice_id):
    merchent = os.getenv("ZARINPAL_MERCHANT_ID")

    authority = request.GET.get('Authority')
    verify_url = 'https://payment.zarinpal.com/pg/v4/payment/verify.json'
    # Fetch the invoice by invoice_id (not order_id, for consistency)
    try:
        invoice = invoices.objects.get(id=invoice_id)
        amount = invoice.amount
    except invoices.DoesNotExist:
        return HttpResponse("فاکتور پیدا نشد. درصورتی که پرداخت کرده اید به پشتیبانی تماس بگید.")

    # Send the verification request to Zarinpal
    response = requests.post(verify_url, json={
        "merchant_id": merchent,
        "amount": amount,
        "authority": authority
    }, headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })

    response_data = response.json()
    data = response_data.get("data", {})

    # Check if payment was successful
    if data.get("code") == 100:
        try:
            # Update invoice status and user tokens
            user = invoice.user_id_id  # Access the related user_data instance through the ForeignKey
            user_datas = user_data.objects.get(id=user)
            if invoice.amount == price.objects.get(option=1).price:
                user_datas.remaining_days += price.objects.get(option=1).days
                user_datas.save()  # Don't forget to save the user's updated token count
            elif invoice.amount == price.objects.get(option=2).price:
                user_datas.remaining_days += price.objects.get(option=2).days
                user_datas.save()  # Don't forget to save the user's updated token count
            invoice.status = "OK"
            invoice.save()
            return HttpResponse(f"status changed to OK, user Token: {user_datas.token}")
        except user_data.DoesNotExist:
            return HttpResponse("کاربر پیدا نشد. درصورتی که مبلغی از حساب شما کم شده است با پشتیبانی تماس بگیرید.")
    else:
        # If payment is not successful, mark the invoice as "NOK"
        invoice.status = "NOK"
        invoice.save()
        return HttpResponse("پرداخت شما موفقیت آمیز نبوده است در صورتی که مبلغی از حساب شما کم شده است بعد از ۴۸ ساعت به حساب شما بازمیگردد.")
