import React, { useEffect, useState } from 'react';
import { Card, CardContent, Typography, CircularProgress, List, ListItem, ListItemText } from '@mui/material';
import axios from 'axios';

const AgentLogs: React.FC = () => {
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('/api/logs')
      .then(res => {
        setLogs(res.data.logs || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <CircularProgress />;

  return (
    <Card>
      <CardContent>
        <Typography variant="h6">Agent Reasoning Logs</Typography>
        <List sx={{ maxHeight: 400, overflow: 'auto' }}>
          {logs.length === 0 && (
            <ListItem><ListItemText primary="No logs yet." /></ListItem>
          )}
          {logs.map((line, idx) => (
            <ListItem key={idx} divider>
              <ListItemText primary={line} />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

export default AgentLogs; 