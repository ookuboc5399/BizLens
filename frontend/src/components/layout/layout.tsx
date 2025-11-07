import React from "react";
import { useLocation } from "react-router-dom";
import Navigation from '../Navigation';
import AIAssistant from '../AIAssistant';


interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) { // supabaseプロップは使用しない
  const location = useLocation();
  
  // ログインページではナビゲーションを表示しない
  const isLoginPage = location.pathname === '/login' || location.pathname === '/admin/login';
  
  // ログインページではAIAssistantも表示しない
  const shouldShowAIAssistant = !isLoginPage;

  return (
    <div className="min-h-screen bg-gray-900 dark">
      {!isLoginPage && <Navigation />}
      <main className="container mx-auto px-4 py-8 text-gray-100">
        {children}
      </main>
      {shouldShowAIAssistant && <AIAssistant />}
    </div>
  );
}