export class GroupOrderSocket {
  constructor(groupId, token, onUpdate) {
    this.groupId = groupId
    this.token = token
    this.onUpdate = onUpdate
    this.ws = null
    this.reconnectTimer = null
    this.retries = 0
    this.maxRetries = 5
    this.disabled = false
  }

  connect() {
    if (this.disabled || this.retries >= this.maxRetries) {
      this.disabled = true
      return
    }

    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    const url = `${wsUrl}/ws/group/${this.groupId}/?token=${this.token}`

    try {
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        console.log('✅ Group WS connected')
        this.retries = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'current_state' || data.type === 'state_update') {
            this.onUpdate(data)
          }
        } catch {}
      }

      this.ws.onclose = () => {
        this.retries++
        if (this.retries < this.maxRetries) {
          this.reconnectTimer = setTimeout(() => this.connect(), 3000)
        }
      }

      this.ws.onerror = () => {}
    } catch {
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