import { cartAPI } from '../api/cart'
import { useCartStore } from '../store/cartStore'
import toast from 'react-hot-toast'

export const useCart = () => {
  const { setCart, clearCart } = useCartStore()

  const refreshCart = async () => {
    try {
      const cart = await cartAPI.getCart()
      setCart(cart)
      return cart
    } catch { return null }
  }

  const addItem = async (menu_item_id, quantity = 1) => {
    try {
      await cartAPI.addToCart(menu_item_id, quantity)
      toast.success('Added to cart! 🛒')
      await refreshCart()
      return true
    } catch { return false }
  }

  const updateQty = async (item_id, quantity) => {
    if (quantity < 1) return removeItem(item_id)
    try {
      await cartAPI.updateItem(item_id, quantity)
      await refreshCart()
    } catch {}
  }

  const removeItem = async (item_id) => {
    try {
      await cartAPI.removeItem(item_id)
      toast.success('Removed from cart')
      await refreshCart()
    } catch {}
  }

  const clearAll = async () => {
    try {
      await cartAPI.clearCart()
      clearCart()
      toast.success('Cart cleared')
    } catch {}
  }

  return { refreshCart, addItem, updateQty, removeItem, clearAll }
}