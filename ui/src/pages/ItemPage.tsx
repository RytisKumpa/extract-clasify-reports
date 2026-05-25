import { useEffect, useState } from "react";
import {
  AcceptReject,
  ExtractedDataDisplay,
  FilePreview,
  useItemData,
  type Highlight,
  type ExtractedData,
  Button,
} from "@llamaindex/ui";
import { Clock, XCircle, Download } from "lucide-react";
import { useParams } from "react-router-dom";
import { useToolbar } from "@/lib/ToolbarContext";
import { useNavigate } from "react-router-dom";
import { modifyJsonSchema } from "@llamaindex/ui/lib";
import { APP_TITLE } from "@/lib/config";
import { downloadExtractedDataItem } from "@/lib/export";
import { useMetadataContext } from "@/lib/MetadataProvider";
import { convertBoundingBoxesToHighlights } from "@/lib/utils";

export default function ItemPage() {
  const { itemId } = useParams<{ itemId: string }>();
  const { setButtons, setBreadcrumbs } = useToolbar();
  const [highlight, setHighlight] = useState<Highlight | undefined>(undefined);
  const { metadata } = useMetadataContext();

  // Use the hook to fetch item data (initially with investment analysis schema)
  const itemHookData = useItemData<any>({
    // Use investment analysis schema as default
    jsonSchema: modifyJsonSchema(metadata.schemas["investment_analysis"] || {}, {}),
    itemId: itemId as string,
    isMock: false,
  });

  // Determine the correct schema based on document type classification
  const classificationData = itemHookData.item?.data as
    | ExtractedData<any>
    | undefined;

  // Handle nested data structure from LlamaCloud Agent Data
  const extractedContent = classificationData?.data as any;
  const actualData = extractedContent?.data || extractedContent;
  const documentType = (
    (classificationData?.metadata?.document_type as string | undefined) ||
    (extractedContent?.metadata?.document_type as string | undefined) ||
    (actualData?.document_metadata?.document_type as string | undefined) ||
    "not_known"
  ).replace(/_/g, " ").toUpperCase(); // Convert "commercial_dd" to "COMMERCIAL DD"

  // For investment analysis, we use a single comprehensive schema
  const correctSchema = metadata.schemas["investment_analysis"];

  // Update the schema in itemHookData if document type is available
  const [schemaKey, setSchemaKey] = useState(0);
  const [appliedSchema, setAppliedSchema] = useState(correctSchema);

  useEffect(() => {
    if (documentType && metadata.schemas["investment_analysis"]) {
      setAppliedSchema(modifyJsonSchema(metadata.schemas["investment_analysis"], {}));
      setSchemaKey(schemaKey + 1);
    }
  }, [documentType, metadata.schemas]);

  const navigate = useNavigate();

  useEffect(() => {
    const classificationData = itemHookData.item?.data as ExtractedData<any> | undefined;
    const extractedContent = classificationData?.data as any;
    const actualData = extractedContent?.data || extractedContent;
    const fileName = classificationData?.file_name || actualData?.file_name;
    if (fileName) {
      setBreadcrumbs([
        { label: APP_TITLE, href: "/" },
        {
          label: fileName,
          isCurrentPage: true,
        },
      ]);
    }

    return () => {
      setBreadcrumbs([{ label: APP_TITLE, href: "/" }]);
    });
  }, [itemHookData.item?.data, setBreadcrumbs]);
  }, [itemHookData.item?.data, setBreadcrumbs]);

  useEffect(() => {
    setButtons(() => [
      <div className="ml-auto flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            if (itemData) {
              downloadExtractedDataItem(itemData);
            }
          }}
          disabled={!itemData}
          startIcon={<Download className="h-4 w-4" />}
          label="Export JSON"
        />
        <AcceptReject<any>>
          itemData={itemHookData}
          onComplete={() => navigate("/")}
        />
      </div>,
    ]);
    return () => {
      setButtons(() => []);
    };
  }, [itemHookData.data, setButtons]);

  const {
    item: itemData,
    updateData,
    loading: isLoading,
    error,
  } = itemHookData;

  const documentTypeReasoning = (
    (classificationData?.metadata?.classification_reasoning as string | undefined) ||
    (extractedContent?.metadata?.classification_reasoning as string | undefined) ||
    (actualData?.classification_reasoning as string | undefined)
  );

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <Clock className="h-8 w-8 animate-spin mx-auto mb-2" />
          <div className="text-sm text-gray-500">Loading investment data...</div>
        </div>
      </div>
    );
  }

  if (error || !itemData) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <XCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
          <div className="text-sm text-gray-500">
            Error loading investment data: {error || "Item not found"}
          </div>
        </div>
      </div>
    );
  }

  // Handle nested data structure from LlamaCloud Agent Data
  const classificationData = itemData.data as ExtractedData<any>;
  const extractedContent = classificationData?.data as any;
  const actualData = extractedContent?.data || extractedContent;

  const extractedData = actualData ? { ...classificationData, data: actualData } : classificationData;
  const fileId = extractedData?.file_id || actualData?.file_id;

  return (
    <div className="flex h-full bg-gray-50">
      <div className="w-1/2 border-r h-full border-gray-200 bg-white">
        {fileId && (
          <FilePreview
            fileId={fileId}
            onBoundingBoxClick={(box, pageNumber) => {
              console.log("Bounding box clicked:", box, "on page:", pageNumber);
            }}
            highlight={highlight}
          />
        )}
      </div>

      <div className="flex-1 bg-white h-full overflow-y-auto">
        <div className="p-4 space-y-4">
          {/* Document Type Classification Info */}
          {documentType && documentType !== "NOT KNOWN" && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
              <div className="text-sm font-semibold text-blue-900">
                Document Type: {documentType}
              </div>
              {documentTypeReasoning && (
                <div className="text-xs text-blue-600 mt-1">
                  {documentTypeReasoning}
                </div>
              )}
            </div>
          )}
          <ExtractedDataDisplay<any>
            key={schemaKey}
            extractedData={extractedData}
            title="Investment Due Diligence Data"
            onChange={(updatedData) => {
              // Handle nested structure when updating data
              const updatedContent = { data: { data: updatedData } };
              updateData(updatedContent);
            }}
            onHoverField={(args) => {
              const highlights = convertBoundingBoxesToHighlights(
                args?.metadata?.citation,
              );
              setHighlight(highlights[0]);
            }}
            jsonSchema={appliedSchema}
          />
        </div>
      </div>
    </div>
  );
}