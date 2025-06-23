import React from 'react';
import { Container, Typography, AppBar, Toolbar, Box, Tabs, Tab } from '@mui/material';
import StatusView from './components/StatusView';
import TimelineView from './components/TimelineView';
import AgentLogs from './components/AgentLogs';
import FeedbackForm from './components/FeedbackForm';

function a11yProps(index: number) {
  return {
    id: `dashboard-tab-${index}`,
    'aria-controls': `dashboard-tabpanel-${index}`,
  };
}

const App: React.FC = () => {
  const [tab, setTab] = React.useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTab(newValue);
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Self-Healing Pipeline Dashboard
          </Typography>
        </Toolbar>
      </AppBar>
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Tabs value={tab} onChange={handleTabChange} aria-label="dashboard tabs">
          <Tab label="Status" {...a11yProps(0)} />
          <Tab label="Timeline" {...a11yProps(1)} />
          <Tab label="Agent Logs" {...a11yProps(2)} />
          <Tab label="Feedback" {...a11yProps(3)} />
        </Tabs>
        <Box sx={{ mt: 2 }}>
          {tab === 0 && <StatusView />}
          {tab === 1 && <TimelineView />}
          {tab === 2 && <AgentLogs />}
          {tab === 3 && <FeedbackForm />}
        </Box>
      </Container>
    </Box>
  );
};

export default App; 