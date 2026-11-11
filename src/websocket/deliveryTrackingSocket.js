export class DeliveryTrackingSocket {
  constructor(orderId, token, onLocationUpdate) {
    this.orderId = orderId
    this.token = token
    this.onLocationUpdate = onLocationUpdate
    this.ws = null
    this.reconnectTimer = null
    this.retries = 0
    this.maxRetries = 3
    this.disabled = false
  }

  connect() {
    if (this.disabled || this.retries >= this.maxRetries) {
      this.disabled = true
      return
    }

    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    const url = `${wsUrl}/ws/delivery/${this.orderId}/tracking/?token=${this.token}`

    try {
      this.ws = new WebSocket(url)

      this.ws.onopen = () => { this.retries = 0 }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.lat && data.lng) {
            this.onLocationUpdate({ lat: data.lat, lng: data.lng, timestamp: data.timestamp })
          }
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

      this.ws.onerror = () => {}
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