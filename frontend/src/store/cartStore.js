import { create } from 'zustand'

export const useCartStore = create((set) => ({
  itemCount: 0,
  cartTotal: 0,
  restaurant: null,

  setCart: (cart) => set({
    itemCount: cart?.item_count || 0,
    cartTotal: cart?.subtotal || 0,
    restaurant: cart?.restaurant || null,
  }),

  clearCart: () => set({ itemCount: 0, cartTotal: 0, restaurant: null }),
}))