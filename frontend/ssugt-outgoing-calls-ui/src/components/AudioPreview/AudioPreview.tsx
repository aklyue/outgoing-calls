import React from "react";
import { Box } from "@mui/material";
import LoadingButton from "@mui/lab/LoadingButton";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import StopIcon from "@mui/icons-material/Stop";
import { useApi } from "../../hooks/useApi/useApi";

import { useAudio } from "../../hooks/useAudio/useAudio";

interface Props {
  template: string;
  rows: any[];
  col: string;
  ttsType: string;
}

const AudioPreview: React.FC<Props> = ({ template, rows, col, ttsType }) => {
  const { synthesize } = useApi();

  const { status, onPlayStop, canPreview, mediaRef } = useAudio({
    template,
    rows,
    col,
    ttsType,
    synthesize,
  });

  return (
    <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
      <LoadingButton
        variant="contained"
        onClick={onPlayStop}
        loading={status === "loading"}
        disabled={!canPreview}
        startIcon={status === "playing" ? <StopIcon /> : <PlayArrowIcon />}
        color={status === "playing" ? "primary" : "primary"}
      >
        {status === "playing" ? "Остановить синтез" : "Прослушать синтез"}
      </LoadingButton>

      <audio ref={mediaRef} preload="auto" style={{ display: "none" }} />
    </Box>
  );
};

export default AudioPreview;
