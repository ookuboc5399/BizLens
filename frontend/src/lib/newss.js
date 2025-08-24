import fetch from "node-fetch";

// Django APIサーバーURL
const SERVERURL = "http://127.0.0.1:8000/";

// 投稿一覧を取得
export async function getAllNewssData() {
  const res = await fetch(new URL(`${SERVERURL}api2/news/`));
  const newss = await res.json();
  return newss;
  
}

// 投稿一覧のIDを取得
export async function getAllNewsIds() {
  const res = await fetch(new URL(`${SERVERURL}api2/news/`));
  const newss = await res.json();
  return newss.map((news) => {
    return {
      params: {
        id: String(news.id),
      },
    };
  });
}

// 投稿詳細を取得
export async function getNewsData(id) {
  const res = await fetch(new URL(`${SERVERURL}api2/news/${id}/`));
  const news = await res.json();
  return news;
}