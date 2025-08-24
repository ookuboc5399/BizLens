import { useState, useEffect } from 'react';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

// グローバル状態変数
let globalUser: any = null;
let globalIsAuthenticated = false;
let globalIsAdmin = false;
let globalIsInitialized = false;

// 状態更新関数
export const updateAuthState = (user: any, isAuthenticated: boolean, isAdmin: boolean) => {
  globalUser = user;
  globalIsAuthenticated = isAuthenticated;
  globalIsAdmin = isAdmin;
  globalIsInitialized = true;
};

export const resetAuthState = () => {
  globalUser = null;
  globalIsAuthenticated = false;
  globalIsAdmin = false;
  globalIsInitialized = true;
};

export const useAuth = (supabase: SupabaseClient) => {
  const [user, setUser] = useState<any>(globalUser);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(globalIsAuthenticated);
  const [isAdmin, setIsAdmin] = useState<boolean>(globalIsAdmin);
  const [isInitialized, setIsInitialized] = useState<boolean>(globalIsInitialized);

  useEffect(() => {
    if (!supabase) {
      setIsInitialized(true);
      return;
    }

    // 初期セッションを取得
    const getInitialSession = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession();
        if (error) {
          console.error('セッション取得エラー:', error);
          updateAuthState(null, false, false);
          setUser(null);
          setIsAuthenticated(false);
          setIsAdmin(false);
          setIsInitialized(true);
          return;
        }

        if (session?.user) {
          const userData = session.user;
          const isAdminUser = userData.user_metadata?.role === 'admin';
          
          updateAuthState(userData, true, isAdminUser);
          setUser(userData);
          setIsAuthenticated(true);
          setIsAdmin(isAdminUser);
        } else {
          updateAuthState(null, false, false);
          setUser(null);
          setIsAuthenticated(false);
          setIsAdmin(false);
        }
        setIsInitialized(true);
      } catch (error) {
        console.error('初期セッション取得エラー:', error);
        updateAuthState(null, false, false);
        setUser(null);
        setIsAuthenticated(false);
        setIsAdmin(false);
        setIsInitialized(true);
      }
    };

    getInitialSession();

    // 認証状態の変更を監視
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (event === 'SIGNED_IN' && session?.user) {
          const userData = session.user;
          const isAdminUser = userData.user_metadata?.role === 'admin';
          
          updateAuthState(userData, true, isAdminUser);
          setUser(userData);
          setIsAuthenticated(true);
          setIsAdmin(isAdminUser);
        } else if (event === 'SIGNED_OUT') {
          updateAuthState(null, false, false);
          setUser(null);
          setIsAuthenticated(false);
          setIsAdmin(false);
        }
        setIsInitialized(true);
      }
    );

    return () => subscription.unsubscribe();
  }, [supabase]);

  return {
    user,
    isAuthenticated,
    isAdmin,
    isInitialized,
    supabase
  };
};