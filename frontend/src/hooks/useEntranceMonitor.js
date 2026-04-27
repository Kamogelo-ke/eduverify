import { useState } from "react";

export const useEntranceMonitor = () => {
  const [scans, setScans] = useState([
    { id: 1, name: "Sambo L.", studentNo: "223506755", status: "Granted", time: "08:54" },
    { id: 2, name: "Khumalo S.M.", studentNo: "222958431", status: "Granted", time: "08:45" },
    { id: 3, name: "Molalatladi K.L.", studentNo: "230403716", status: "Override", time: "08:42" },
    { id: 4, name: "Khoza K.", studentNo: "219084322", status: "Denied", time: "08:40" },
  ]);

  const stats = {
    total: 42,
    granted: 38,
    denied: 3,
    overrides: 1
  };

  return { scans, stats };
};