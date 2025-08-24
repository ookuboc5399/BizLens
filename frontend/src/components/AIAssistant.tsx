import { useState } from 'react';
import { ChatBubbleLeftIcon, XMarkIcon } from '@heroicons/react/24/outline';

function AIAssistant() {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // 既存のstate宣言...

  return (
    <div 
      className={`fixed bottom-4 right-4 transition-all duration-300 ${
        isExpanded 
          ? 'w-96 h-[600px]' 
          : 'w-16 h-16 rounded-full cursor-pointer hover:bg-gray-100'
      }`}
      onClick={() => !isExpanded && setIsExpanded(true)}
    >
      {isExpanded ? (
        <div className="bg-white rounded-lg shadow-lg p-4 h-full relative">
          {/* 閉じるボタン */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(false);
            }}
            className="absolute top-2 right-2 text-gray-500 hover:text-gray-700"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
          
          {/* 既存のフォームコンテンツ */}
          <div className="h-full flex flex-col">
            {/* チャット履歴とフォーム... */}
          </div>
        </div>
      ) : (
        <div className="w-full h-full flex items-center justify-center">
          <ChatBubbleLeftIcon className="w-8 h-8 text-blue-500" />
        </div>
      )}
    </div>
  );
}

export default AIAssistant; 