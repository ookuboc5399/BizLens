
import { Link } from 'react-router-dom';

function Navigation() {
  return (
    <nav className="bg-gray-800 text-white">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="font-bold text-xl">Market Analysis</Link>
          <div className="flex space-x-4">
            <Link to="/company-search" className="hover:text-red-500">企業検索</Link>
            <Link to="/company-comparison" className="hover:text-red-500">企業比較</Link>
            <Link to="/financial-reports" className="hover:text-red-500">決算説明資料</Link>
            <Link to="/earnings-calendar" className="hover:text-red-500">決算予定カレンダー</Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navigation; 