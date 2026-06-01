import { useEffect } from 'react';
import ReviewPanel from '../components/ReviewPanel';
import { useTradeStore } from '../stores/tradeStore';

export default function Review() {
  const { userId, setUserId } = useTradeStore();

  useEffect(() => {
    if (!userId) {
      setUserId(1);
    }
  }, [userId, setUserId]);

  return (
    <div>
      {userId && <ReviewPanel userId={userId} />}
    </div>
  );
}
