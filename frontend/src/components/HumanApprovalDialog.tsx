import React from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography } from '@mui/material';

interface HumanApprovalDialogProps {
  open: boolean;
  fixDescription: string;
  onApprove: () => void;
  onReject: () => void;
}

const HumanApprovalDialog: React.FC<HumanApprovalDialogProps> = ({ open, fixDescription, onApprove, onReject }) => {
  return (
    <Dialog open={open} onClose={onReject}>
      <DialogTitle>Approve Automated Fix?</DialogTitle>
      <DialogContent>
        <Typography gutterBottom>
          The system has suggested the following automated fix:
        </Typography>
        <Typography color="primary" sx={{ fontWeight: 500, mb: 2 }}>
          {fixDescription}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Do you approve applying this fix?
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onReject} color="secondary" variant="outlined">Reject</Button>
        <Button onClick={onApprove} color="primary" variant="contained">Approve</Button>
      </DialogActions>
    </Dialog>
  );
};

export default HumanApprovalDialog;
