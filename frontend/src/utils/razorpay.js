export const loadRazorpayScript = () => {
  return new Promise((resolve) => {
    if (window.Razorpay) return resolve(true)
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.onload = () => resolve(true)
    script.onerror = () => resolve(false)
    document.body.appendChild(script)
  })
}

export const openRazorpayCheckout = ({
  razorpay_key_id,
  razorpay_order_id,
  amount,
  currency = 'INR',
  name,
  description,
  prefill = {},
  onSuccess,
  onFailure,
}) => {
  const options = {
    key: razorpay_key_id,
    amount,
    currency,
    name: 'HongKong 🥡',
    description,
    order_id: razorpay_order_id,
    prefill,
    theme: { color: '#FFC72C' },
    handler: (response) => onSuccess(response),
    modal: {
      ondismiss: () => onFailure({ reason: 'cancelled' }),
    },
  }
  const rzp = new window.Razorpay(options)
  rzp.open()
  rzp.on('payment.failed', (response) => onFailure(response.error))
}