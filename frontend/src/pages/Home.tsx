
import { HomeTradingViewChart } from '../components/HomeTradingViewChart';
import { MarketDataDisplay } from '../components/MarketDataDisplay';
import { NewsDisplay } from '../components/NewsDisplay';
import TradingViewTickerTape from '../components/TradingViewTickerTape';


function Home() {
  return (
    <div className="text-white">
      <div className="container mx-auto px-4 py-8">
        <div className="relative">
          {/* ティッカーテープ */}
          <div className="mb-8">
            <TradingViewTickerTape />
          </div>
          
          {/* メインチャートエリア */}
          <div className="bg-gray-800 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-bold mb-4">日経平均株価</h2>
            <div className="w-full h-[400px]">
              <HomeTradingViewChart symbol="NIKKEI" />
            </div>
          </div>

          {/* サブチャートグリッド */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* マーケット概況 */}
            <div className="bg-gray-800 rounded-lg p-4 lg:col-span-2">
              <h3 className="text-lg font-bold mb-4">マーケット概況</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-semibold mb-2">主要指数</h4>
                  <MarketDataDisplay type="market-data" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold mb-2">出来高分析</h4>
                  <MarketDataDisplay type="volume-analysis" />
                </div>
              </div>
            </div>


            {/* ニュースフィード */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-lg font-bold mb-4">最新ニュース</h3>
              <NewsDisplay />
            </div>

            {/* 市場カレンダー */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-lg font-bold mb-4">市場カレンダー</h3>
              <div className="space-y-2">
                <div className="text-sm">
                  <div className="text-gray-400">本日の予定</div>
                  <div>決算発表 5社</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;
