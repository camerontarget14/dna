import {
  Flex,
  Text,
  Button,
  Card,
  Badge,
  TextArea,
  Box,
  Select,
} from "@radix-ui/themes";
import { useDNAFramework } from "./hooks/useDNAFramework";
import { useShotGrid } from "./hooks/useShotGrid";
import { useState, useEffect } from "react";
import { ConnectionStatus } from "../../shared/dna-frontend-framework";
import { useGetVersions } from "./hooks/useGetVersions";

export default function App() {
  const toreviewversions = useGetVersions();
  const {
    framework,
    connectionStatus,
    setVersion,
    setUserNotes,
    setAiNotes,
    addVersions,
    getTranscriptText,
    generateNotes,
    state,
  } = useDNAFramework();
  const shotgrid = useShotGrid();
  const [meetingId, setMeetingId] = useState("");
  const [generatingNotesId, setGeneratingNotesId] = useState<string | null>(
    null,
  );
  const [uploadingCSV, setUploadingCSV] = useState(false);

  // Populate framework with versions from useGetVersions on mount
  useEffect(() => {
    const versionData = Object.entries(toreviewversions).map(
      ([id, version]) => ({
        id: Number(id),
        context: {
          ...version,
          description: version.description || `Version ${id}`,
        },
      }),
    );
    addVersions(versionData);
  }, []);

  // Load playlist items manually with button
  const handleLoadPlaylist = async () => {
    if (!shotgrid.selectedPlaylistId) return;

    try {
      const items = await shotgrid.fetchPlaylistItems(
        shotgrid.selectedPlaylistId,
      );

      // Clear existing versions first
      framework.clearVersions();

      // Convert playlist items to versions
      const versionData = items.map((item, index) => ({
        id: Date.now() + index, // Generate unique IDs
        context: {
          description: item,
        },
      }));

      // Add new versions
      addVersions(versionData);

      alert(`Loaded ${items.length} items from playlist`);
    } catch (error) {
      console.error("Error loading playlist:", error);
      alert("Failed to load playlist items");
    }
  };

  const handleJoinMeeting = () => {
    if (meetingId.trim()) {
      framework.joinMeeting(meetingId);
    }
  };

  const handleLeaveMeeting = () => {
    framework.leaveMeeting();
  };

  const handleCSVUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadingCSV(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("http://localhost:8000/upload-playlist", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();

        // Clear existing versions
        framework.clearVersions();

        // Convert CSV items to versions
        const versionData = data.items.map((item: string, index: number) => ({
          id: Date.now() + index,
          context: {
            description: item,
          },
        }));

        addVersions(versionData);
        alert(`Loaded ${data.items.length} items from CSV`);
      } else {
        const error = await response.json();
        alert(`Failed to upload CSV: ${error.detail || "Unknown error"}`);
      }
    } catch (error) {
      console.error("Error uploading CSV:", error);
      alert("Failed to upload CSV. Make sure the backend is running.");
    } finally {
      setUploadingCSV(false);
      // Reset the input so the same file can be uploaded again
      event.target.value = "";
    }
  };

  const handleCSVExport = () => {
    if (versions.length === 0) {
      alert("No versions to export");
      return;
    }

    // Create CSV content
    const headers = ["Version Name", "Notes", "LLM Notes", "Transcript"];
    const rows = versions.map((version) => {
      const versionName =
        version.context.description || `Version ${version.id}`;
      const notes = version.userNotes || "";
      const llmNotes = version.aiNotes || "";
      const transcript = getTranscriptText(version.id);

      // Escape fields that contain commas, quotes, or newlines
      const escapeCSV = (field: string) => {
        if (
          field.includes(",") ||
          field.includes('"') ||
          field.includes("\n")
        ) {
          return `"${field.replace(/"/g, '""')}"`;
        }
        return field;
      };

      return [
        escapeCSV(versionName),
        escapeCSV(notes),
        escapeCSV(llmNotes),
        escapeCSV(transcript),
      ].join(",");
    });

    const csvContent = [headers.join(","), ...rows].join("\n");

    // Create blob and download
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);

    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `dna-notes-${new Date().toISOString().slice(0, 10)}.csv`,
    );
    link.style.visibility = "hidden";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getStatusColor = (status: ConnectionStatus) => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return "green";
      case ConnectionStatus.CONNECTING:
        return "yellow";
      case ConnectionStatus.DISCONNECTED:
      case ConnectionStatus.CLOSED:
        return "red";
      case ConnectionStatus.ERROR:
        return "red";
      default:
        return "gray";
    }
  };

  // Get versions from the framework state
  const versions = state.versions;
  return (
    <Flex direction="column" gap="4" p="4">
      <Flex direction="row" gap="3" align="center">
        <Text size="5" weight="bold">
          Dailies Notes Assistant
        </Text>
        <Badge color={getStatusColor(connectionStatus)}>
          {connectionStatus ? connectionStatus.toUpperCase() : "Unknown"}
        </Badge>
      </Flex>

      <Flex direction="row" gap="4" wrap="wrap">
        <Card size="2" style={{ flex: 1, minWidth: 300, maxWidth: 400 }}>
          <Flex direction="column" gap="3" p="4">
            <Text size="4" weight="bold">
              Join Meeting
            </Text>
            <Flex direction="column" gap="2">
              <label htmlFor="meeting-id">Meeting ID</label>
              <input
                id="meeting-id"
                type="text"
                placeholder="Enter meeting ID or URL"
                value={meetingId}
                onChange={(e) => setMeetingId(e.target.value)}
                disabled={connectionStatus !== ConnectionStatus.DISCONNECTED}
                style={{
                  padding: "8px 12px",
                  border: "1px solid #ccc",
                  borderRadius: "4px",
                  fontSize: "14px",
                }}
              />
            </Flex>
            {connectionStatus !== ConnectionStatus.CONNECTED && (
              <Button
                onClick={handleJoinMeeting}
                disabled={
                  !meetingId.trim() ||
                  connectionStatus !== ConnectionStatus.DISCONNECTED
                }
                size="2"
              >
                Join Meeting
              </Button>
            )}

            {connectionStatus === ConnectionStatus.CONNECTED && (
              <Button onClick={handleLeaveMeeting} size="2" color="red">
                Leave Meeting
              </Button>
            )}
          </Flex>
        </Card>

        <Card size="2" style={{ flex: 1, minWidth: 300, maxWidth: 400 }}>
          <Flex direction="column" gap="3" p="4">
            <Text size="4" weight="bold">
              CSV Playlist
            </Text>
            <Text size="2" color="gray">
              Upload a CSV file with version names in the first column (header
              row will be skipped)
            </Text>
            <Flex direction="column" gap="2">
              <input
                id="csv-upload"
                type="file"
                accept=".csv"
                onChange={handleCSVUpload}
                disabled={uploadingCSV}
                style={{ display: "none" }}
              />
              <Button
                onClick={() => document.getElementById("csv-upload")?.click()}
                disabled={uploadingCSV}
                size="2"
              >
                {uploadingCSV ? "Uploading..." : "Import CSV"}
              </Button>
              <Button
                onClick={handleCSVExport}
                disabled={versions.length === 0}
                size="2"
                variant="outline"
              >
                Export CSV
              </Button>
            </Flex>
          </Flex>
        </Card>

        {shotgrid.isEnabled && (
          <Card size="2" style={{ flex: 1, minWidth: 300, maxWidth: 400 }}>
            <Flex direction="column" gap="3" p="4">
              <Text size="4" weight="bold">
                ShotGrid Integration
              </Text>
              <Flex direction="column" gap="2">
                <label htmlFor="sg-project">Project</label>
                <Select.Root
                  value={shotgrid.selectedProjectId}
                  onValueChange={shotgrid.setSelectedProjectId}
                  disabled={shotgrid.loading || shotgrid.projects.length === 0}
                >
                  <Select.Trigger placeholder="Select Project" />
                  <Select.Content>
                    {shotgrid.projects.map((project) => (
                      <Select.Item key={project.id} value={String(project.id)}>
                        {project.code}
                      </Select.Item>
                    ))}
                  </Select.Content>
                </Select.Root>
              </Flex>
              <Flex direction="column" gap="2">
                <label htmlFor="sg-playlist">Playlist</label>
                <Select.Root
                  value={shotgrid.selectedPlaylistId}
                  onValueChange={shotgrid.setSelectedPlaylistId}
                  disabled={
                    !shotgrid.selectedProjectId ||
                    shotgrid.loading ||
                    shotgrid.playlists.length === 0
                  }
                >
                  <Select.Trigger placeholder="Select Playlist" />
                  <Select.Content>
                    {shotgrid.playlists.map((playlist) => (
                      <Select.Item
                        key={playlist.id}
                        value={String(playlist.id)}
                      >
                        {playlist.code} ({playlist.created_at?.slice(0, 10)})
                      </Select.Item>
                    ))}
                  </Select.Content>
                </Select.Root>
              </Flex>
              <Button
                onClick={handleLoadPlaylist}
                disabled={!shotgrid.selectedPlaylistId || shotgrid.loading}
                size="2"
              >
                Load Playlist
              </Button>
              {shotgrid.loading && (
                <Text size="1" color="gray">
                  Loading...
                </Text>
              )}
              {shotgrid.error && (
                <Text size="1" color="red">
                  {shotgrid.error}
                </Text>
              )}
            </Flex>
          </Card>
        )}
      </Flex>

      {versions.map((version) => (
        <Card key={version.id} size="2" style={{ marginTop: 16 }}>
          <Flex direction="row" gap="4" p="4">
            <Flex direction="column" gap="2" style={{ minWidth: 150 }}>
              <Text size="3" weight="bold">
                Version ID: {version.id}
              </Text>
              <Text size="2">
                {version.context.description ? (
                  version.context.description
                ) : (
                  <em>No description</em>
                )}
              </Text>
              <Button
                onClick={async () => {
                  setGeneratingNotesId(version.id);
                  try {
                    const notes = await generateNotes(Number(version.id));
                    setAiNotes(Number(version.id), notes);
                  } catch (error) {
                    console.error("Error generating notes:", error);
                    alert(
                      "Failed to generate notes. Check console for details.",
                    );
                  } finally {
                    setGeneratingNotesId(null);
                  }
                }}
                disabled={generatingNotesId === version.id}
                size="2"
              >
                {generatingNotesId === version.id
                  ? "Generating..."
                  : "Generate AI Notes"}
              </Button>
            </Flex>
            <Box mt="2" style={{ flex: 1 }}>
              <label htmlFor={`user-notes-${version.id}`}>User Notes</label>
              <TextArea
                onFocus={() =>
                  setVersion(Number(version.id), { ...version.context })
                }
                id={`user-notes-${version.id}`}
                value={version.userNotes || ""}
                onChange={(e) =>
                  setUserNotes(Number(version.id), e.target.value)
                }
                placeholder="Enter your notes for this version"
                style={{ minWidth: 250, minHeight: 200, marginTop: 4 }}
              />
            </Box>
            <Box mt="2" style={{ flex: 1 }}>
              <label htmlFor={`ai-notes-${version.id}`}>
                AI Generated Notes
              </label>
              <TextArea
                id={`ai-notes-${version.id}`}
                value={version.aiNotes || ""}
                placeholder="AI generated notes will appear here..."
                readOnly
                style={{ minWidth: 250, minHeight: 200, marginTop: 4 }}
              />
              <Flex justify="end" style={{ marginTop: 8 }}>
                <Button
                  size="1"
                  onClick={() => {
                    const currentUserNotes = version.userNotes || "";
                    const separator = currentUserNotes ? "\n\n" : "";
                    setUserNotes(
                      Number(version.id),
                      currentUserNotes + separator + (version.aiNotes || ""),
                    );
                  }}
                  disabled={!version.aiNotes}
                >
                  Add to Notes
                </Button>
              </Flex>
            </Box>
            <Box mt="2" style={{ flex: 1 }}>
              <label htmlFor={`transcript-${version.id}`}>Transcript</label>
              <TextArea
                onFocus={() =>
                  setVersion(Number(version.id), { ...version.context })
                }
                id={`transcript-${version.id}`}
                value={getTranscriptText(version.id)}
                placeholder="Transcript will appear here as it's received..."
                readOnly
                style={{ minWidth: 500, minHeight: 200, marginTop: 4 }}
              />
            </Box>
          </Flex>
        </Card>
      ))}
    </Flex>
  );
}
