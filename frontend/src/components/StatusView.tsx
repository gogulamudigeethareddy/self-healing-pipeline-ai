import React, { useEffect, useState } from 'react';
import { Card, CardContent, Typography, CircularProgress, List, ListItem, ListItemText, Snackbar, Alert } from '@mui/material';
import axios from 'axios';
import HumanApprovalDialog from './HumanApprovalDialog';

const StatusView: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [pendingFix, setPendingFix] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Poll for pipeline status
  useEffect(() => {
    const fetchStatus = () => {
      axios.get('/api/status')
        .then(res => {
          setStatus(res.data);
          setLoading(false);
        })
        .catch(() => {
          setLoading(false);
          setError('Failed to load pipeline status.');
        });
    };
    fetchStatus();
    const poll = setInterval(fetchStatus, 5000);
    return () => clearInterval(poll);
  }, []);

  // Poll for pending fix every 3 seconds
  useEffect(() => {
    const poll = setInterval(() => {
      axios.get('/api/pending_fix')
        .then(res => setPendingFix(res.data))
        .catch(() => setPendingFix(null));
    }, 3000);
    return () => clearInterval(poll);
  }, []);

  const handleApprove = () => {
    axios.post('/api/approve_fix')
      .then(() => {
        setPendingFix(null);
        setSuccess('Fix approved and applied.');
      })
      .catch(() => setError('Failed to approve fix.'));
  };

  const handleReject = () => {
    setPendingFix(null);
    setSuccess('Fix rejected.');
  };

  if (loading) return <CircularProgress />;
  if (!status) return <Typography color="error">Failed to load status.</Typography>;

  return (
    <>
      <Card>
        <CardContent>
          <Typography variant="h6">Recent Pipeline Runs</Typography>
          <List>
            {status.pipeline_runs && status.pipeline_runs.length === 0 && (
              <ListItem><ListItemText primary="No runs yet." /></ListItem>
            )}
            {status.pipeline_runs && status.pipeline_runs.map((run: any, idx: number) => (
              <ListItem key={idx} divider>
                <ListItemText
                  primary={`Run at ${run.timestamp}`}
                  secondary={`Monitor: ${run.monitor?.status}, Diagnosis: ${run.diagnosis?.root_cause || 'N/A'}, Fix: ${run.fix?.status || 'N/A'}`}
                />
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>
      <HumanApprovalDialog
        open={!!pendingFix && !!pendingFix.pending_fix && !pendingFix.approved}
        fixDescription={pendingFix?.pending_fix || ''}
        onApprove={handleApprove}
        onReject={handleReject}
      />
      <Snackbar open={!!error} autoHideDuration={4000} onClose={() => setError(null)}>
        <Alert severity="error" onClose={() => setError(null)}>{error}</Alert>
      </Snackbar>
      <Snackbar open={!!success} autoHideDuration={3000} onClose={() => setSuccess(null)}>
        <Alert severity="success" onClose={() => setSuccess(null)}>{success}</Alert>
      </Snackbar>
    </>
  );
};

export default StatusView;