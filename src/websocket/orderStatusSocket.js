export class OrderStatusSocket {
  constructor(orderId, token, onMessage) {
    this.orderId = orderId
    this.token = token
    this.onMessage = onMessage
    this.ws = null
    this.reconnectTimer = null
    this.retries = 0
    this.maxRetries = 3
    this.disabled = false
  }

  connect() {
    if (this.disabled || this.retries >= this.maxRetries) {
      console.warn('⚠️ WebSocket disabled (backend not supporting WS). Page refresh for updates.')
      this.disabled = true
      return
    }

    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    const url = `${wsUrl}/ws/orders/${this.orderId}/status/?token=${this.token}`

    try {
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        console.log('✅ Order status WS connected')
        this.retries = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.onMessage(data)
        } catch (err) {}
      }

      this.ws.onclose = () => {
        this.retries++
        if (this.retries < this.maxRetries) {
          this.reconnectTimer = setTimeout(() => this.connect(), 5000)
        } else {
          this.disabled = true
        }
      }

      this.ws.onerror = () => {
        // Silent fail
      }
    } catch (err) {
      this.disabled = true
    }
  }

  disconnect() {
    this.disabled = true
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    if (this.ws) {
      this.ws.onclose = null
      this.ws.close()
    }
  }
}