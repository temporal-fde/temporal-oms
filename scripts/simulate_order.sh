xh PUT http://localhost:8080/api/v1/commerce-app/orders/order-123 customerId="cust-001" order:='{"orderId":"order-123","items":[{"itemId":"shirt-001","quantity":1}],"shippingAddress":{"street":"123 Main St","city":"New York","state":"NY","postalCode":"10001","country":"US"}}'

xh POST http://localhost:8080/api/v1/payments-app/orders customerId="cust-001" rrn="payment-intent-456" amountCents=9999 metadata:='{"orderId":"order-123"}'
