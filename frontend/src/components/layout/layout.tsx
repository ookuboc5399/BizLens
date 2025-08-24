import React from "react";
import Navigation from '../Navigation';
import AIAssistant from '../AIAssistant';
import { SupabaseClient } from '@supabase/supabase-js'; // SupabaseClientをインポート

interface LayoutProps {
  children: React.ReactNode;
  supabase: SupabaseClient; // supabaseプロップを追加
}

export function Layout({ children, supabase }: LayoutProps) { // supabaseプロップを受け取る

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