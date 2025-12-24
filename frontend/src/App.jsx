import { useState, useEffect } from 'react'

function App() {
    const [dataTamu, setDataTamu] = useState([])
    const [serverStatus, setServerStatus] = useState(false)
    const [selectedTamu, setSelectedTamu] = useState(null)

    const API_URL = "http://192.168.0.118:5000"

    // --- LOGIC HEARTBEAT (BARU) ---
    useEffect(() => {
        // Fungsi untuk kirim sinyal "Saya masih disini"
        const sendHeartbeat = async () => {
            try {
                await fetch(`${API_URL}/api/heartbeat`, { method: 'POST' })
            } catch (err) {
                // Biarkan saja kalau error (misal server mati)
            }
        }

        // Kirim pertama kali saat buka
        sendHeartbeat()

        // Kirim setiap 3 detik
        const interval = setInterval(sendHeartbeat, 3000)

        return () => clearInterval(interval)
    }, [])
    // -----------------------------

    // Logic Fetch Data (Sama seperti sebelumnya)
    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch(`${API_URL}/api/data`)
                const data = await response.json()
                setDataTamu(data)
                setServerStatus(true)
                if (!selectedTamu && data.length > 0) {
                    setSelectedTamu(data[0])
                }
            } catch (error) {
                console.error("Gagal konek:", error)
                setServerStatus(false)
            }
        }
        fetchData()
        const interval = setInterval(fetchData, 2000)
        return () => clearInterval(interval)
    }, [selectedTamu]) 

    // ... (SISA KODE UI KE BAWAH SAMA PERSIS) ...
    return (
        <div className="min-h-screen bg-slate-950 p-4 md:p-8 font-sans text-slate-200">
             {/* ... UI Bos yang tadi ... */}
             {/* Saya tidak copy paste ulang UI nya karena tidak berubah */}
             {/* Langsung tutup komponen utama */}
             <div className="max-w-7xl mx-auto space-y-8">
                {/* 1. HEADER */}
                <div className="flex justify-between items-end border-b border-slate-800 pb-6">
                    <div>
                        <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight">
                            Smart <span className="text-cyan-400">Doorbell</span>
                        </h1>
                        <div className="flex items-center gap-2 mt-2">
                            <span className="relative flex h-3 w-3">
                                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${serverStatus ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
                                <span className={`relative inline-flex rounded-full h-3 w-3 ${serverStatus ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
                            </span>
                            <p className="text-sm text-slate-400 font-mono">
                                {serverStatus ? "SYSTEM ONLINE" : "CONNECTION LOST"}
                            </p>
                        </div>
                    </div>
                    {/* ... */}
                </div>

                {/* 2. MONITORING & 3. TABEL (SAMA) */}
                 <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* KIRI: LIVE CAMERA STREAM */}
                    <div className="bg-black rounded-3xl overflow-hidden shadow-2xl border border-slate-800 relative group h-[400px]">
                        <div className="absolute top-4 left-4 z-10 flex gap-2">
                            <span className="bg-red-600 text-white text-[10px] font-bold px-2 py-1 rounded animate-pulse">
                                ● LIVE
                            </span>
                            <span className="bg-black/50 backdrop-blur text-white text-[10px] font-bold px-2 py-1 rounded">
                                CAM 01
                            </span>
                        </div>
                        <img 
                            src={`${API_URL}/video_feed`} 
                            className="w-full h-full object-cover bg-slate-900"
                            alt="Live Stream" 
                        />
                    </div>
                     {/* KANAN */}
                     <div className="flex flex-col h-[400px]">
                        {selectedTamu ? (
                            <HeroSection tamu={selectedTamu} apiUrl={API_URL} />
                        ) : (
                            <div className="h-full bg-slate-900 rounded-3xl border border-slate-800 flex items-center justify-center text-slate-500 flex-col gap-2">
                                <span className="loading loading-spinner loading-lg"></span>
                                <span>Menunggu Data Log...</span>
                            </div>
                        )}
                    </div>
                 </div>

                 {/* TABEL */}
                 <div className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
                     {/* ... Isi Tabel Sama ... */}
                    <div className="p-6 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
                        <h2 className="font-bold text-white text-lg">Riwayat Deteksi</h2>
                    </div>
                    <div className="overflow-x-auto max-h-[400px] overflow-y-auto custom-scrollbar">
                        <table className="w-full text-left text-sm text-slate-400">
                            <thead className="bg-slate-950 uppercase text-xs font-semibold text-slate-500 sticky top-0 z-10">
                                <tr>
                                    <th className="px-6 py-4 bg-slate-950">Waktu</th>
                                    <th className="px-6 py-4 bg-slate-950">Foto</th>
                                    <th className="px-6 py-4 bg-slate-950">Nama</th>
                                    <th className="px-6 py-4 bg-slate-950">Status Deteksi</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {dataTamu.map((tamu, index) => (
                                    <TableRow 
                                        key={index} 
                                        tamu={tamu} 
                                        apiUrl={API_URL} 
                                        onClick={() => setSelectedTamu(tamu)}
                                        isSelected={selectedTamu && selectedTamu.waktu === tamu.waktu}
                                    />
                                ))}
                            </tbody>
                        </table>
                    </div>
                 </div>
             </div>
        </div>
    )
}

// ... (Sub Komponen HeroSection & TableRow SAMA PERSIS dengan kode sebelumnya)
function HeroSection({ tamu, apiUrl }) {
    const isAman = tamu.status.includes('Aman')
    return (
        <div className="h-full bg-slate-900/50 rounded-3xl p-6 border border-slate-800 flex flex-col justify-center relative overflow-hidden transition-all duration-500">
            <div className={`absolute top-0 right-0 w-64 h-64 blur-[100px] opacity-20 pointer-events-none ${isAman ? 'bg-emerald-500' : 'bg-rose-600'}`}></div>
            <div className="flex items-start justify-between mb-4 z-10">
                <div>
                    <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Log Terpilih</p>
                    <h2 className="text-3xl font-bold text-white line-clamp-1">{tamu.nama}</h2>
                </div>
                <span className={`px-3 py-1 text-xs font-bold rounded border ${isAman ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' : 'text-rose-400 border-rose-500/30 bg-rose-500/10'}`}>
                    {tamu.status}
                </span>
            </div>
            <div className="relative w-full flex-grow bg-slate-950 rounded-2xl overflow-hidden border border-slate-800 group shadow-inner">
                <img src={`${apiUrl}/foto/${tamu.file_foto}`} className="w-full h-full object-cover opacity-90 group-hover:opacity-100 group-hover:scale-105 transition duration-500" alt="Log Foto" onError={(e) => {e.target.src="https://placehold.co/600x400?text=No+Data"}} />
            </div>
            <div className="mt-4 pt-4 border-t border-slate-800 text-slate-400 text-sm font-mono flex items-center gap-2">
                <span>🕒</span>{new Date(tamu.waktu).toLocaleString()}
            </div>
        </div>
    )
}

function TableRow({ tamu, apiUrl, onClick, isSelected }) {
    const isAman = tamu.status.includes('Aman')
    const badgeStyle = isAman ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20';
    const dotStyle = isAman ? 'bg-emerald-500' : 'bg-rose-500';

    return (
        <tr onClick={onClick} className={`cursor-pointer transition duration-200 border-l-4 ${isSelected ? 'bg-slate-800 border-cyan-400' : 'hover:bg-slate-900 border-transparent'}`}>
            <td className="px-6 py-4 font-mono text-slate-300">{new Date(tamu.waktu).toLocaleTimeString()}</td>
            <td className="px-6 py-4"><img src={`${apiUrl}/foto/${tamu.file_foto}`} className={`h-10 w-10 rounded-full object-cover ring-2 ${isSelected ? 'ring-cyan-400' : 'ring-slate-700'}`} alt="thumb"/></td>
            <td className={`px-6 py-4 font-medium ${isSelected ? 'text-cyan-400' : 'text-white'}`}>{tamu.nama}</td>
            <td className="px-6 py-4">
                 <span className={`inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-medium border ${badgeStyle}`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${dotStyle}`}></span>{tamu.status}
                 </span>
            </td>
        </tr>
    )
}

export default App