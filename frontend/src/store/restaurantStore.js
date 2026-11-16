import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useRestaurantStore = create(
  persist(
    (set) => ({
      selectedRestaurant: null,
      setRestaurant: (restaurant) => set({ selectedRestaurant: restaurant }),
      clearRestaurant: () => set({ selectedRestaurant: null }),
    }),
    { name: 'hongkong-restaurant' }
  )
)