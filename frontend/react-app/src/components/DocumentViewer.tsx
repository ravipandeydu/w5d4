import React, { useState, useEffect } from "react";
import { Box, Paper, Typography, CircularProgress } from "@mui/material";
import { Document, Page } from "react-pdf";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { materialDark } from "react-syntax-highlighter/dist/esm/styles/prism";

interface DocumentViewerProps {
  documentId: string;
  fileType: string;
  content: any;
}

const DocumentViewer: React.FC<DocumentViewerProps> = ({
  documentId,
  fileType,
  content,
}) => {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
  }, [documentId]);

  const renderContent = () => {
    switch (fileType) {
      case "pdf":
        return (
          <Document
            file={content}
            onLoadSuccess={({ numPages }) => {
              setNumPages(numPages);
              setLoading(false);
            }}
          >
            <Page pageNumber={pageNumber} />
          </Document>
        );

      case "image":
        return (
          <Box
            component="img"
            src={content}
            alt="Document"
            sx={{ maxWidth: "100%", height: "auto" }}
            onLoad={() => setLoading(false)}
          />
        );

      case "code":
        return (
          <SyntaxHighlighter
            language="javascript"
            style={materialDark}
            onLoad={() => setLoading(false)}
          >
            {content}
          </SyntaxHighlighter>
        );

      case "table":
        return (
          <Box sx={{ overflowX: "auto" }}>
            <table>
              <tbody>
                {content.map((row: any[], rowIndex: number) => (
                  <tr key={rowIndex}>
                    {row.map((cell: any, cellIndex: number) => (
                      <td key={cellIndex}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </Box>
        );

      default:
        return (
          <Typography
            variant="body1"
            component="pre"
            sx={{ whiteSpace: "pre-wrap" }}
          >
            {content}
          </Typography>
        );
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 2, height: "100%", overflow: "auto" }}>
      {loading ? (
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          height="100%"
        >
          <CircularProgress />
        </Box>
      ) : (
        <Box>
          {renderContent()}
          {fileType === "pdf" && numPages && (
            <Box mt={2} display="flex" justifyContent="center">
              <Typography>
                Page {pageNumber} of {numPages}
              </Typography>
            </Box>
          )}
        </Box>
      )}
    </Paper>
  );
};

export default DocumentViewer;
