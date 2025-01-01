import React from "react";
import Navigation from '../Navigation';
import AIAssistant from '../AIAssistant';
import { useAuth } from '../../hooks/useAuth';
import { Link } from "react-router-dom";

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { isAdmin } = useAuth();

  return (
    <div className="min-h-screen bg-gray-900 dark">
      <Navigation />
      <main className="container mx-auto px-4 py-8 text-gray-100">
        {children}
      </main>
      <AIAssistant />
      {isAdmin && (
        <div className="admin-menu fixed bottom-4 right-4 bg-gray-800 p-4 rounded-lg shadow-lg">
          <h3 className="menu-title text-lg font-semibold text-gray-100 mb-2">管理者メニュー</h3>
          <Link 
            to="/admin/data-collection"
            className="text-blue-400 hover:text-blue-300 transition-colors"
          >
            データ収集
          </Link>
        </div>
      )}
    </div>
  );
}
