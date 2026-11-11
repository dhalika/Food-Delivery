import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { groupOrderAPI } from '../../api/groupOrder'
import { Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function CreateGroupOrder() {
  const navigate = useNavigate()
  const location = useLocation()
  const restaurantId = location.state?.restaurant_id

  useEffect(() => {
    if (!restaurantId) {
      navigate('/customer')
      return
    }
    createGroup()
  }, [])

  const createGroup = async () => {
    try {
      const res = await groupOrderAPI.create(restaurantId)
      toast.success(`Group created! Code: ${res.share_code}`)
      navigate(`/customer/group/${res.share_code}`)
    } catch {
      navigate('/customer')
    }
  }

  return (
    <div className="flex items-center justify-center py-20">
      <div className="text-center">
        <Loader2 className="animate-spin text-brand-500 mx-auto mb-4" size={48} />
        <p className="font-semibold text-dark">Creating group order...</p>
      </div>
    </div>
  )
}