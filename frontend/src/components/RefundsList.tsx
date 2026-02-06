import { useFailedRefunds } from '../api/appointments';
import { useRetryRefund } from '../api/actions';

export function RefundsList() {
  const { data: refunds = [], isLoading } = useFailedRefunds();
  const retryMutation = useRetryRefund();

  if (isLoading) return <div className="text-gray-500">Loading...</div>;
  if (refunds.length === 0) return null;

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-semibold text-red-700 mb-3">
        Failed Refunds ({refunds.length})
      </h3>

      <div className="space-y-2">
        {refunds.map(refund => (
          <div key={refund.id} className="flex justify-between items-center p-2 bg-red-50 rounded">
            <div>
              <div className="font-medium">{refund.patient_name}</div>
              <div className="text-sm text-gray-600">
                {refund.appointment_date} | Rs {refund.amount_paise / 100}
              </div>
              <div className="text-xs text-gray-500">
                Retries: {refund.retry_count} | Status: {refund.status}
              </div>
            </div>
            <button
              onClick={() => {
                if (confirm('Retry this refund?')) {
                  retryMutation.mutate(refund.id);
                }
              }}
              disabled={retryMutation.isPending}
              className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50"
            >
              {retryMutation.isPending ? 'Retrying...' : 'Retry'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
