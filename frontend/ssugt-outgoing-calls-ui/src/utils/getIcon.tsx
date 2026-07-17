import EditIcon from "@mui/icons-material/Edit";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PauseIcon from "@mui/icons-material/Pause";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import LoginIcon from "@mui/icons-material/Login";
import HistoryIcon from "@mui/icons-material/History";
export const getIcon = (action: string) => {
  const act = action.toLowerCase();
  const iconProps = { sx: { fontSize: 22 }, color: "info" as const };
  if (act.includes("create")) return <AddCircleIcon {...iconProps} />;
  if (act.includes("update")) return <EditIcon {...iconProps} />;
  if (act.includes("delete")) return <DeleteOutlineIcon {...iconProps} />;
  if (act.includes("login")) return <LoginIcon {...iconProps} />;
  if (act.includes("pause")) return <PauseIcon {...iconProps} />;
  if (act.includes("resume")) return <PlayArrowIcon {...iconProps} />;
  return <HistoryIcon {...iconProps} />;
};
