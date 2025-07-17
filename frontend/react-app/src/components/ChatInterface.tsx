import React, { useState, useRef, useEffect } from "react";
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Divider,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import AttachFileIcon from "@mui/icons-material/AttachFile";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  sources?: string[];
}

interface ChatInterfaceProps {
  onSendMessage: (message: string, imageData?: string) => Promise<void>;
  messages: Message[];
  loading: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  onSendMessage,
  messages,
  loading,
}) => {
  const [input, setInput] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && !imageFile) return;

    let imageData;
    if (imageFile) {
      imageData = await convertImageToBase64(imageFile);
    }

    await onSendMessage(input, imageData);
    setInput("");
    setImageFile(null);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith("image/")) {
      setImageFile(file);
    }
  };

  const convertImageToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  return (
    <Paper
      elevation={3}
      sx={{ height: "100%", display: "flex", flexDirection: "column" }}
    >
      <Box sx={{ flexGrow: 1, overflow: "auto", p: 2 }}>
        <List>
          {messages.map((message, index) => (
            <React.Fragment key={message.id}>
              <ListItem
                sx={{
                  flexDirection: "column",
                  alignItems:
                    message.role === "user" ? "flex-end" : "flex-start",
                  mb: 2,
                }}
              >
                <Box
                  sx={{
                    maxWidth: "70%",
                    backgroundColor:
                      message.role === "user" ? "primary.main" : "grey.200",
                    color: message.role === "user" ? "white" : "text.primary",
                    borderRadius: 2,
                    p: 2,
                  }}
                >
                  <Typography variant="body1">{message.content}</Typography>
                  {message.sources && (
                    <Box mt={1}>
                      <Typography variant="caption" color="text.secondary">
                        Sources: {message.sources.join(", ")}
                      </Typography>
                    </Box>
                  )}
                </Box>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ mt: 0.5 }}
                >
                  {new Date(message.timestamp).toLocaleTimeString()}
                </Typography>
              </ListItem>
              {index < messages.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
        {loading && (
          <Box display="flex" justifyContent="center" my={2}>
            <CircularProgress size={24} />
          </Box>
        )}
        <div ref={endOfMessagesRef} />
      </Box>

      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{
          p: 2,
          backgroundColor: "background.paper",
          borderTop: 1,
          borderColor: "divider",
        }}
      >
        {imageFile && (
          <Box mb={1}>
            <Typography variant="caption" color="text.secondary">
              Selected image: {imageFile.name}
            </Typography>
          </Box>
        )}
        <Box display="flex" gap={1}>
          <input
            type="file"
            accept="image/*"
            style={{ display: "none" }}
            ref={fileInputRef}
            onChange={handleFileSelect}
          />
          <IconButton
            color="primary"
            onClick={() => fileInputRef.current?.click()}
            size="small"
          >
            <AttachFileIcon />
          </IconButton>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Ask a question..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            size="small"
          />
          <IconButton
            color="primary"
            type="submit"
            disabled={loading || (!input.trim() && !imageFile)}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Box>
    </Paper>
  );
};

export default ChatInterface;
