import React, { useState } from 'react';
import { Card, CardContent, Typography, TextField, Button, Box, Rating, Snackbar, Alert } from '@mui/material';
import axios from 'axios';

const FeedbackForm: React.FC = () => {
  const [feedback, setFeedback] = useState('');
  const [rating, setRating] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rating) {
      setError('Please provide a rating.');
      return;
    }
    try {
      await axios.post('/api/feedback', { feedback, rating });
      setSubmitted(true);
      setFeedback('');
      setRating(null);
      setError('');
    } catch {
      setError('Failed to submit feedback.');
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6">Rate the Fix</Typography>
        <form onSubmit={handleSubmit}>
          <Box sx={{ mb: 2 }}>
            <Rating
              name="fix-rating"
              value={rating}
              onChange={(_, value) => setRating(value)}
            />
          </Box>
          <TextField
            label="Feedback (optional)"
            multiline
            rows={3}
            value={feedback}
            onChange={e => setFeedback(e.target.value)}
            fullWidth
            sx={{ mb: 2 }}
          />
          <Button type="submit" variant="contained" color="primary">
            Submit
          </Button>
        </form>
        <Snackbar open={!!error} autoHideDuration={4000} onClose={() => setError('')}>
          <Alert severity="error" onClose={() => setError('')}>{error}</Alert>
        </Snackbar>
        <Snackbar open={submitted} autoHideDuration={4000} onClose={() => setSubmitted(false)}>
          <Alert severity="success" onClose={() => setSubmitted(false)}>Thank you for your feedback!</Alert>
        </Snackbar>
      </CardContent>
    </Card>
  );
};

export default FeedbackForm; 