import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App"
// import "antd/dist/reset.css" // antdがインストールされていないためコメントアウト
import "./index.css"
import { createClient } from "@supabase/supabase-js"; // Supabaseをインポート

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App supabase={supabase} /> {/* Appコンポーネントにsupabaseインスタンスを渡す */}
  </React.StrictMode>,
)