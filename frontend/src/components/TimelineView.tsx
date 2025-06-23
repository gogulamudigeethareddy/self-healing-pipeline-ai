import React, { useEffect, useState } from 'react';
import { Card, CardContent, Typography, CircularProgress, List, ListItem, ListItemText, Divider } from '@mui/material';
import axios from 'axios';

const TimelineView: React.FC = () => {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('/api/status')
      .then(res => {
        setRuns(res.data.pipeline_runs || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <CircularProgress />;

  return (
    <Card>
      <CardContent>
        <Typography variant="h6">Failure & Fix Timeline</Typography>
        <List>
          {runs.length === 0 && (
            <ListItem><ListItemText primary="No events yet." /></ListItem>
          )}
          {runs.map((run, idx) => (
            <React.Fragment key={idx}>
              <ListItem>
                <ListItemText
                  primary={`[${run.timestamp}]`}
                  secondary={
                    <>
                      <div>Monitor: {run.monitor?.status}</div>
                      <div>Diagnosis: {run.diagnosis?.root_cause || 'N/A'}</div>
                      <div>Fix: {run.fix?.status || 'N/A'}</div>
                    </>
                  }
                />
              </ListItem>
              {idx < runs.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

export default TimelineView; 