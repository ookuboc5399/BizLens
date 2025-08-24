import React from "react";
import Navigation from '../Navigation';
import AIAssistant from '../AIAssistant';


interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) { // supabaseプロップは使用しない

  return (
    <div className="min-h-screen bg-gray-900 dark">
      <Navigation />
      <main className="container mx-auto px-4 py-8 text-gray-100">
        {children}
      </main>
      <AIAssistant />
    </div>
  );
}