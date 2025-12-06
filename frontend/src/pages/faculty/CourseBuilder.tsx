import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Plus, Settings, Upload, Network } from "lucide-react";
import { apiClient } from "@/api/client";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { Course, Concept } from "@/types";

export default function CourseBuilder() {
  const { courseId } = useParams<{ courseId: string }>();
  const [activeTab, setActiveTab] = useState<
    "concepts" | "materials" | "settings"
  >("concepts");

  const { data: course } = useQuery({
    queryKey: ["course", courseId],
    queryFn: () => apiClient.get<Course>(`/courses/${courseId}`),
    enabled: courseId !== "new",
  });

  const { data: concepts } = useQuery({
    queryKey: ["concepts", courseId],
    queryFn: () => apiClient.get<Concept[]>(`/courses/${courseId}/concepts`),
    enabled: courseId !== "new",
  });

  if (courseId === "new") {
    return <NewCourseForm />;
  }

  return (
    <div className="min-h-screen bg-muted/30">
      <header className="bg-background border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" asChild>
              <Link to="/faculty">
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <div>
              <h1 className="text-xl font-bold">
                {course?.name || "Loading..."}
              </h1>
              <p className="text-sm text-muted-foreground">
                {course?.description}
              </p>
            </div>
          </div>
        </div>
        <div className="container mx-auto px-4">
          <nav className="flex gap-4 border-t pt-2">
            {[
              { id: "concepts", label: "Concepts", icon: Network },
              { id: "materials", label: "Materials", icon: Upload },
              { id: "settings", label: "Settings", icon: Settings },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as typeof activeTab)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-[2px] ${
                  activeTab === id
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {activeTab === "concepts" && <ConceptsTab concepts={concepts || []} />}
        {activeTab === "materials" && <MaterialsTab />}
        {activeTab === "settings" && <SettingsTab />}
      </main>
    </div>
  );
}

function NewCourseForm() {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  return (
    <div className="min-h-screen bg-muted/30 flex items-center justify-center">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Create New Course</CardTitle>
          <CardDescription>
            Set up your course basics to get started
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Course Name</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Introduction to Data Engineering"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Description</label>
            <textarea
              className="w-full min-h-[100px] px-3 py-2 border rounded-md"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Course description..."
            />
          </div>
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link to="/faculty">Cancel</Link>
            </Button>
            <Button>Create Course</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ConceptsTab({ concepts }: { concepts: Concept[] }) {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold">Knowledge Graph</h2>
        <Button size="sm">
          <Plus className="h-4 w-4 mr-2" />
          Add Concept
        </Button>
      </div>

      {concepts.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center py-12">
            <Network className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              No concepts yet. Add your first concept to build the knowledge
              graph.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {concepts.map((concept) => (
            <Card key={concept.id}>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">{concept.name}</CardTitle>
                <CardDescription>{concept.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4 text-sm text-muted-foreground">
                  <span>
                    Difficulty: {concept.difficulty_level || "Not set"}
                  </span>
                  <span>
                    Est. time: {concept.estimated_time_minutes || "Not set"} min
                  </span>
                  <span>Prerequisites: {concept.prerequisites.length}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function MaterialsTab() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold">Course Materials</h2>
        <Button size="sm">
          <Upload className="h-4 w-4 mr-2" />
          Upload Material
        </Button>
      </div>
      <Card>
        <CardContent className="flex flex-col items-center py-12">
          <Upload className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            Upload PDFs, documents, or lecture notes to build your course
            content.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function SettingsTab() {
  return (
    <div className="space-y-6 max-w-2xl">
      <h2 className="text-lg font-semibold">Course Settings</h2>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Pedagogy Configuration</CardTitle>
          <CardDescription>
            Configure how the AI tutor interacts with students
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Teaching Style</label>
            <select className="w-full px-3 py-2 border rounded-md">
              <option value="socratic">Socratic</option>
              <option value="guided_discovery">Guided Discovery</option>
              <option value="direct_instruction">Direct Instruction</option>
              <option value="worked_examples">Worked Examples</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Base Model</label>
            <select className="w-full px-3 py-2 border rounded-md">
              <option value="llama-3.1-8b">Llama 3.1 8B</option>
              <option value="llama-3.1-70b">Llama 3.1 70B</option>
              <option value="mistral-7b">Mistral 7B</option>
            </select>
          </div>
          <Button>Save Settings</Button>
        </CardContent>
      </Card>
    </div>
  );
}
