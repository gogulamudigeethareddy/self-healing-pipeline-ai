import React, { useEffect, useState } from 'react';
import { Card, CardContent, Typography, CircularProgress, List, ListItem, ListItemText } from '@mui/material';
import axios from 'axios';

const StatusView: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('/api/status')
      .then(res => {
        setStatus(res.data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <CircularProgress />;
  if (!status) return <Typography color="error">Failed to load status.</Typography>;

  return (
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
  );
};

export default StatusView; 