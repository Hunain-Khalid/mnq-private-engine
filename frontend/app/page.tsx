'use client';

import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CandlestickSeries, createSeriesMarkers, IChartApi, ISeriesApi } from 'lightweight-charts';
import axios from 'axios';

export default function Home() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  const [resolution, setResolution] = useState('1m');
  const [mode, setMode] = useState('price');
  const [dataCount, setDataCount] = useState(0);
  const API_BASE_URL = 'http://127.0.0.1:8000'; // Using IP instead of localhost solves 99% of WSL2 network binding bugs


  const fetchData = (res: string, m: string) => {
    // Around line 17 inside frontend/app/page.tsx -> Update port to 8001
    // Calls Next.js proxy instead of raw FastAPI port
    axios.get(`/api/proxy/candles?resolution=${res}&mode=${m}&limit=50000`)
      .then(response => {
        // Safe check for data integrity
        if (!response.data || !response.data.candles) {
          console.warn("Received empty or malformed data payload:", response.data);
          return;
        }

        const { candles, markers } = response.data;

        const formattedData = candles.map((item: any) => ({
          time: item.time,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
        }));

        if (seriesRef.current) {
          seriesRef.current.setData(formattedData);

          // Render sample execution marks onto the canvas
          if (markers && markers.length > 0) {
            createSeriesMarkers(seriesRef.current, markers);
          }

          chartRef.current?.timeScale().fitContent();
        }

        setDataCount(formattedData.length);
      })
      .catch(err => {
        console.error("Fetch failed:", err);
      });
  };

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#131722' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#1f293d' },
        horzLines: { color: '#1f293d' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 600,
    });

    chartRef.current = chart;

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    seriesRef.current = candlestickSeries;

    fetchData(resolution, mode);

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  const handleResolutionChange = (res: string) => {
    setResolution(res);
    fetchData(res, mode);
  };

  const handleModeToggle = () => {
    const newMode = mode === 'price' ? 'log_return' : 'price';
    setMode(newMode);
    fetchData(resolution, newMode);
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-12 bg-gray-950 text-white font-mono">
      <div className="w-full max-w-6xl">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold">🏛️ Alpha Flush Node // Institutional Deck</h1>
            <p className="text-xs text-gray-400 mt-1">
              Streaming <span className="text-green-400 font-bold">{dataCount}</span> bars from DuckDB | Mode: <span className="text-yellow-400 uppercase">{mode}</span>
            </p>
          </div>

          <div className="flex gap-3 items-center">
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-1 flex gap-1">
              {['1m', '15m', '1h'].map((res) => (
                <button
                  key={res}
                  onClick={() => handleResolutionChange(res)}
                  className={`px-3 py-1 text-xs rounded-md font-bold transition-all ${resolution === res ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
                    }`}
                >
                  {res.toUpperCase()}
                </button>
              ))}
            </div>

            <button
              onClick={handleModeToggle}
              className="bg-yellow-600 hover:bg-yellow-500 text-black px-4 py-1.5 rounded-lg text-xs font-bold transition-all"
            >
              Toggle: {mode === 'price' ? 'Show Log-Returns' : 'Show Absolute Price'}
            </button>
          </div>
        </div>

        <div ref={chartContainerRef} className="w-full rounded-xl overflow-hidden shadow-2xl border border-gray-800" />
      </div>
    </main>
  );
}
