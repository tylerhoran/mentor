import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../../components/ui/card";

interface ClassOverview {
  course_id: string;
  course_name: string;
  total_students: number;
  active_students_7d: number;
  total_interactions: number;
  avg_mastery: number;
  concept_stats: ConceptStat[];
  engagement_trend: EngagementPoint[];
  at_risk_students: AtRiskStudent[];
}

interface ConceptStat {
  concept_id: string;
  concept_name: string;
  avg_mastery: number;
  student_count: number;
  struggling_count: number;
}

interface EngagementPoint {
  date: string;
  active_students: number;
  interactions: number;
}

interface AtRiskStudent {
  student_id: string;
  full_name: string;
  email: string;
  risk_factors: string[];
  last_active: string | null;
  avg_mastery: number;
}

export default function Analytics() {
  const { courseId } = useParams<{ courseId: string }>();
  const [timeRange, setTimeRange] = useState<"7d" | "30d" | "90d">("30d");

  const { data: overview, isLoading } = useQuery({
    queryKey: ["analytics", courseId, timeRange],
    queryFn: () =>
      api.get<ClassOverview>(`/analytics/class/${courseId}?range=${timeRange}`),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!overview) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No analytics data available</p>
      </div>
    );
  }

  const getMasteryColor = (level: number) => {
    if (level >= 0.8) return "text-green-600";
    if (level >= 0.6) return "text-yellow-600";
    if (level >= 0.4) return "text-orange-600";
    return "text-red-600";
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <Link
          to={`/faculty/courses/${courseId}`}
          className="text-blue-600 hover:underline text-sm"
        >
          &larr; Back to Course
        </Link>
      </div>

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Class Analytics</h1>
          <p className="text-gray-500">{overview.course_name}</p>
        </div>
        <div className="flex gap-2">
          {(["7d", "30d", "90d"] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1 rounded text-sm ${
                timeRange === range
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {range === "7d"
                ? "7 Days"
                : range === "30d"
                  ? "30 Days"
                  : "90 Days"}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-gray-900">
              {overview.total_students}
            </div>
            <div className="text-sm text-gray-500">Total Students</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-gray-900">
              {overview.active_students_7d}
            </div>
            <div className="text-sm text-gray-500">Active (7 days)</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-gray-900">
              {overview.total_interactions.toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">Total Interactions</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div
              className={`text-3xl font-bold ${getMasteryColor(overview.avg_mastery)}`}
            >
              {Math.round(overview.avg_mastery * 100)}%
            </div>
            <div className="text-sm text-gray-500">Avg Mastery</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Engagement Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Engagement Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-end justify-between gap-1">
              {overview.engagement_trend.map((point, idx) => {
                const maxInteractions = Math.max(
                  ...overview.engagement_trend.map((p) => p.interactions),
                );
                const height =
                  maxInteractions > 0
                    ? (point.interactions / maxInteractions) * 100
                    : 0;
                return (
                  <div key={idx} className="flex-1 flex flex-col items-center">
                    <div
                      className="w-full bg-blue-500 rounded-t"
                      style={{
                        height: `${height}%`,
                        minHeight: point.interactions > 0 ? "4px" : "0",
                      }}
                      title={`${point.date}: ${point.interactions} interactions`}
                    />
                    {idx % 7 === 0 && (
                      <div className="text-xs text-gray-400 mt-1 transform -rotate-45 origin-top-left">
                        {new Date(point.date).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* At-Risk Students */}
        <Card>
          <CardHeader>
            <CardTitle>At-Risk Students</CardTitle>
          </CardHeader>
          <CardContent>
            {overview.at_risk_students.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                No at-risk students identified
              </p>
            ) : (
              <div className="space-y-3">
                {overview.at_risk_students.slice(0, 5).map((student) => (
                  <Link
                    key={student.student_id}
                    to={`/faculty/courses/${courseId}/students/${student.student_id}`}
                    className="block p-3 border rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium text-gray-900">
                          {student.full_name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {student.email}
                        </div>
                      </div>
                      <span
                        className={`text-sm font-medium ${getMasteryColor(student.avg_mastery)}`}
                      >
                        {Math.round(student.avg_mastery * 100)}%
                      </span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {student.risk_factors.map((factor) => (
                        <span
                          key={factor}
                          className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded"
                        >
                          {factor}
                        </span>
                      ))}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Concept Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Concept Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium text-gray-700">
                    Concept
                  </th>
                  <th className="text-center py-3 px-4 font-medium text-gray-700">
                    Students
                  </th>
                  <th className="text-center py-3 px-4 font-medium text-gray-700">
                    Avg Mastery
                  </th>
                  <th className="text-center py-3 px-4 font-medium text-gray-700">
                    Struggling
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">
                    Distribution
                  </th>
                </tr>
              </thead>
              <tbody>
                {overview.concept_stats.map((concept) => (
                  <tr
                    key={concept.concept_id}
                    className="border-b last:border-0 hover:bg-gray-50"
                  >
                    <td className="py-3 px-4">
                      <div className="font-medium text-gray-900">
                        {concept.concept_name}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center text-gray-600">
                      {concept.student_count}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`font-medium ${getMasteryColor(concept.avg_mastery)}`}
                      >
                        {Math.round(concept.avg_mastery * 100)}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      {concept.struggling_count > 0 ? (
                        <span className="text-red-600 font-medium">
                          {concept.struggling_count}
                        </span>
                      ) : (
                        <span className="text-gray-400">0</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            concept.avg_mastery >= 0.8
                              ? "bg-green-500"
                              : concept.avg_mastery >= 0.6
                                ? "bg-yellow-500"
                                : "bg-red-500"
                          }`}
                          style={{ width: `${concept.avg_mastery * 100}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
