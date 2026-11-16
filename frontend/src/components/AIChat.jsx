import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Sparkles, Plus } from 'lucide-react';
import { customerAPI } from '../api/customer';
import { useNavigate } from 'react-router-dom';
import { useCartStore } from '../store/cartStore';

const AIChat = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    {
      type: 'ai',
      text: '👋 Hi! I\'m your AI food assistant. Tell me what you\'re craving — like "spicy chicken under 300" or "healthy breakfast"!',
    },
  ]);

  const messagesEndRef = useRef(null);
  const navigate = useNavigate();
  const addToCart = useCartStore((state) => state.addToCart);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async () => {
    const query = input.trim();
    if (!query || loading) return;

    // Add user message
    setMessages((prev) => [...prev, { type: 'user', text: query }]);
    setInput('');
    setLoading(true);

    try {
      const response = await customerAPI.aiRecommend(query);
      const data = response.data || response;

      if (data.success && data.recommendations?.length > 0) {
        setMessages((prev) => [
          ...prev,
          {
            type: 'ai',
            text: `Here are my top ${data.count} picks for you:`,
            recommendations: data.recommendations,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            type: 'ai',
            text: 'Sorry, I couldn\'t find matching items. Try different keywords!',
          },
        ]);
      }
    } catch (error) {
      console.error('AI error:', error);
      setMessages((prev) => [
        ...prev,
        {
          type: 'ai',
          text: '⚠️ Oops! Something went wrong. Please try again.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleAddToCart = (item) => {
    addToCart({
      id: item.item_id,
      name: item.name,
      price: item.price,
      image_url: item.image_url,
      restaurant_id: item.restaurant_id,
      restaurant_name: item.restaurant_name,
      quantity: 1,
    });

    // Confirm feedback
    setMessages((prev) => [
      ...prev,
      { type: 'system', text: `✅ ${item.name} added to cart!` },
    ]);
  };

  const handleViewRestaurant = (restaurantId) => {
    setIsOpen(false);
    navigate(`/customer/restaurant/${restaurantId}`);
  };

  return (
    <>
      {/* Floating Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 bg-yellow-400 hover:bg-yellow-500 text-black rounded-full p-4 shadow-2xl transition-all hover:scale-110 flex items-center gap-2"
        >
          <Sparkles className="w-6 h-6" />
          <span className="hidden md:inline font-semibold">AI Assistant</span>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-[90vw] max-w-md h-[600px] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border-2 border-yellow-400">
          {/* Header */}
          <div className="bg-yellow-400 text-black p-4 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5" />
              <div>
                <h3 className="font-bold">AI Food Assistant</h3>
                <p className="text-xs opacity-75">Powered by HongKong AI</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="hover:bg-yellow-500 rounded-full p-1 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            {messages.map((msg, idx) => (
              <div key={idx}>
                {msg.type === 'user' && (
                  <div className="flex justify-end">
                    <div className="bg-yellow-400 text-black px-4 py-2 rounded-2xl rounded-br-sm max-w-[80%]">
                      {msg.text}
                    </div>
                  </div>
                )}

                {msg.type === 'ai' && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-gray-200 px-4 py-2 rounded-2xl rounded-bl-sm max-w-[85%] shadow-sm">
                      <p className="text-gray-800">{msg.text}</p>

                      {/* Recommendation Cards */}
                      {msg.recommendations && (
                        <div className="mt-3 space-y-2">
                          {msg.recommendations.map((item) => (
                            <div
                              key={item.item_id}
                              className="border border-gray-200 rounded-lg p-3 bg-gradient-to-r from-yellow-50 to-white hover:shadow-md transition"
                            >
                              <div className="flex gap-3">
                                {item.image_url && (
                                  <img
                                    src={item.image_url}
                                    alt={item.name}
                                    className="w-16 h-16 object-cover rounded-lg flex-shrink-0"
                                    onError={(e) => (e.target.style.display = 'none')}
                                  />
                                )}
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-start justify-between gap-2">
                                    <h4 className="font-semibold text-sm text-gray-900 truncate">
                                      {item.name}
                                    </h4>
                                    <span className={`text-xs px-1 rounded ${item.is_veg ? 'text-green-600' : 'text-red-600'}`}>
                                      {item.is_veg ? '🟢' : '🔴'}
                                    </span>
                                  </div>
                                  <button
                                    onClick={() => handleViewRestaurant(item.restaurant_id)}
                                    className="text-xs text-gray-500 hover:text-yellow-600 hover:underline"
                                  >
                                    {item.restaurant_name} ⭐ {item.restaurant_rating.toFixed(1)}
                                  </button>
                                  <p className="text-xs text-gray-600 italic mt-1 line-clamp-2">
                                    💡 {item.ai_reason}
                                  </p>
                                  <div className="flex items-center justify-between mt-2">
                                    <span className="font-bold text-yellow-600">
                                      ₹{item.price}
                                    </span>
                                    <button
                                      onClick={() => handleAddToCart(item)}
                                      className="bg-yellow-400 hover:bg-yellow-500 text-black text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1 transition"
                                    >
                                      <Plus className="w-3 h-3" />
                                      Add
                                    </button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {msg.type === 'system' && (
                  <div className="flex justify-center">
                    <div className="bg-green-100 text-green-700 text-xs px-3 py-1 rounded-full">
                      {msg.text}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Typing indicator */}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 px-4 py-3 rounded-2xl rounded-bl-sm shadow-sm">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Suggestions */}
          {messages.length === 1 && (
            <div className="px-4 py-2 bg-gray-50 border-t border-gray-100">
              <p className="text-xs text-gray-500 mb-2">Try asking:</p>
              <div className="flex flex-wrap gap-2">
                {['Spicy under ₹300', 'Veg biryani', 'Something sweet'].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setInput(suggestion)}
                    className="text-xs bg-yellow-100 hover:bg-yellow-200 text-yellow-800 px-2 py-1 rounded-full transition"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="p-3 border-t border-gray-200 bg-white flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="What are you craving?"
              disabled={loading}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:border-yellow-400 text-sm"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="bg-yellow-400 hover:bg-yellow-500 disabled:bg-gray-300 text-black rounded-full p-2 transition"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default AIChat;