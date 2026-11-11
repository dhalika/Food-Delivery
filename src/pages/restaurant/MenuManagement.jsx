import { useEffect, useState } from 'react'
import { restaurantAPI } from '../../api/restaurant'
import { useRestaurantStore } from '../../store/restaurantStore'
import { Loader2, Plus, Trash2, Edit, ToggleLeft, ToggleRight, X } from 'lucide-react'
import toast from 'react-hot-toast'

export default function MenuManagement() {
  const { selectedRestaurant } = useRestaurantStore()
  const [categories, setCategories] = useState([])
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCatForm, setShowCatForm] = useState(false)
  const [showItemForm, setShowItemForm] = useState(false)
  const [catName, setCatName] = useState('')
  const [itemForm, setItemForm] = useState({ name: '', price: '', description: '', category_id: '', is_veg: true })

  useEffect(() => { if (selectedRestaurant) load() }, [selectedRestaurant])

  const load = async () => {
    setLoading(true)
    try {
      const [c, i] = await Promise.all([
        restaurantAPI.listCategories(selectedRestaurant.id),
        restaurantAPI.listMenuItems(selectedRestaurant.id),
      ])
      setCategories(c.categories || [])
      setItems(i.items || [])
    } finally { setLoading(false) }
  }

  const handleAddCategory = async (e) => {
    e.preventDefault()
    try {
      await restaurantAPI.createCategory(selectedRestaurant.id, { name: catName })
      toast.success('Category added')
      setShowCatForm(false)
      setCatName('')
      load()
    } catch {}
  }

  const handleAddItem = async (e) => {
    e.preventDefault()
    try {
      await restaurantAPI.createMenuItem(selectedRestaurant.id, {
        ...itemForm,
        price: parseFloat(itemForm.price),
      })
      toast.success('Item added')
      setShowItemForm(false)
      setItemForm({ name: '', price: '', description: '', category_id: '', is_veg: true })
      load()
    } catch {}
  }

  const handleToggle = async (id) => {
    try {
      await restaurantAPI.toggleItemAvailability(id)
      load()
    } catch {}
  }

  const handleDeleteItem = async (id) => {
    if (!confirm('Delete this item?')) return
    try {
      await restaurantAPI.deleteMenuItem(id)
      toast.success('Deleted')
      load()
    } catch {}
  }

  if (!selectedRestaurant) return <div className="card text-center">Select a restaurant first</div>
  if (loading) return <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-500" size={32} /></div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-display font-bold">Menu Management</h1>
        <div className="flex gap-2">
          <button onClick={() => setShowCatForm(true)} className="btn-secondary text-sm"><Plus size={16} className="inline" /> Category</button>
          <button onClick={() => setShowItemForm(true)} className="btn-primary text-sm"><Plus size={16} className="inline" /> Menu Item</button>
        </div>
      </div>

      {/* Category Form */}
      {showCatForm && (
        <div className="card">
          <div className="flex justify-between mb-3"><h3 className="font-bold">New Category</h3><X onClick={() => setShowCatForm(false)} className="cursor-pointer" /></div>
          <form onSubmit={handleAddCategory} className="flex gap-2">
            <input required value={catName} onChange={(e) => setCatName(e.target.value)} placeholder="e.g. Starters" className="input-field flex-1" />
            <button type="submit" className="btn-primary">Add</button>
          </form>
        </div>
      )}

      {/* Item Form */}
      {showItemForm && (
        <div className="card">
          <div className="flex justify-between mb-3"><h3 className="font-bold">New Menu Item</h3><X onClick={() => setShowItemForm(false)} className="cursor-pointer" /></div>
          <form onSubmit={handleAddItem} className="space-y-3">
            <input required value={itemForm.name} onChange={(e) => setItemForm({ ...itemForm, name: e.target.value })} placeholder="Item name" className="input-field" />
            <textarea value={itemForm.description} onChange={(e) => setItemForm({ ...itemForm, description: e.target.value })} placeholder="Description" rows={2} className="input-field resize-none" />
            <div className="grid grid-cols-2 gap-3">
              <input required type="number" min="1" value={itemForm.price} onChange={(e) => setItemForm({ ...itemForm, price: e.target.value })} placeholder="Price (₹)" className="input-field" />
              <select value={itemForm.category_id} onChange={(e) => setItemForm({ ...itemForm, category_id: e.target.value })} className="input-field">
                <option value="">Select Category</option>
                {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={itemForm.is_veg} onChange={(e) => setItemForm({ ...itemForm, is_veg: e.target.checked })} />
              Vegetarian
            </label>
            <button type="submit" className="btn-primary w-full">Add Item</button>
          </form>
        </div>
      )}

      {/* Items List */}
      {items.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-muted">No items yet. Add your first menu item!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.id} className="card flex items-center gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`w-4 h-4 border-2 ${item.is_veg ? 'border-success' : 'border-danger'} flex items-center justify-center`}>
                    <span className={`w-2 h-2 rounded-full ${item.is_veg ? 'bg-success' : 'bg-danger'}`}></span>
                  </span>
                  <h4 className="font-bold">{item.name}</h4>
                  {item.category && <span className="text-xs bg-cream px-2 py-0.5 rounded">{item.category.name}</span>}
                </div>
                <p className="text-sm text-muted mb-1">{item.description}</p>
                <p className="font-bold">₹{item.price}</p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => handleToggle(item.id)} className={`p-2 rounded-lg ${item.is_available ? 'text-success' : 'text-muted'}`} title={item.is_available ? 'Available' : 'Unavailable'}>
                  {item.is_available ? <ToggleRight size={28} /> : <ToggleLeft size={28} />}
                </button>
                <button onClick={() => handleDeleteItem(item.id)} className="p-2 text-danger hover:bg-red-50 rounded-lg">
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}