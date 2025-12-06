import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/client';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';

interface StudentDetail {
  id: string;
  email: string;
  full_name: string;
  enrolled_at: string;
  last_active: string | null;
  total_interactions: number;
  total_time_minutes: number;
  concept_masteries: ConceptMastery[];
  recent_sessions: SessionSummary[];
  gaming_flags: GamingFlag[];
}

interface ConceptMastery {
  concept_id: string;
  concept_name: string;
  mastery_level: number;
  attempts: number;
  last_interaction: string | null;
}

interface SessionSummary {
  id: string;
  started_at: string;
  ended_at: string | null;
  message_count: number;
  concepts_covered: string[];
}

interface GamingFlag {
  id: string;
  detected_at: string;
  signal_type: string;
  severity: string;
  details: string;
}

export default function StudentView() {
  const { courseId, studentId } = useParams<{ courseId: string; studentId: string }>();
  const [activeTab, setActiveTab] = useState<'overview' | 'mastery' | 'sessions' | 'flags'>('overview');

  const { data: student, isLoading } = useQuery({
    queryKey: ['student', courseId, studentId],
    queryFn: () => api.get<StudentDetail>(`/students/${courseId}/${studentId}`),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!student) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Student not found</p>
      </div>
    );
  }

  const getMasteryColor = (level: number) => {
    if (level >= 0.8) return 'bg-green-500';
    if (level >= 0.6) return 'bg-yellow-500';
    if (level >= 0.4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6">
        <Link to={`/faculty/courses/${courseId}`} className="text-blue-600 hover:underline text-sm">
          &larr; Back to Course
        </Link>
      </div>

      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{student.full_name}</h1>
          <p className="text-gray-500">{student.email}</p>
          <p className="text-sm text-gray-400 mt-1">
            Enrolled {new Date(student.enrolled_at).toLocaleDateString()}
          </p>
        </div>
        <Button variant="outline">
          Generate Verification Report
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-gray-900">{student.total_interactions}</div>
            <div className="text-sm text-gray-500">Total Interactions</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-gray-900">{student.total_time_minutes}</div>
            <div className="text-sm text-gray-500">Minutes Engaged</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-gray-900">
              {student.concept_masteries.filter(c => c.mastery_level >= 0.8).length}
              <span className="text-sm font-normal text-gray-400">
                /{student.concept_masteries.length}
              </span>
            </div>
            <div className="text-sm text-gray-500">Concepts Mastered</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-gray-900">{student.gaming_flags.length}</div>
            <div className="text-sm text-gray-500">Gaming Flags</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {(['overview', 'mastery', 'sessions', 'flags'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Learning Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {student.concept_masteries.slice(0, 5).map((concept) => (
                  <div key={concept.concept_id}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-700">{concept.concept_name}</span>
                      <span className="text-gray-500">{Math.round(concept.mastery_level * 100)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getMasteryColor(concept.mastery_level)}`}
                        style={{ width: `${concept.mastery_level * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              {student.concept_masteries.length > 5 && (
                <button
                  onClick={() => setActiveTab('mastery')}
                  className="text-blue-600 text-sm mt-4 hover:underline"
                >
                  View all {student.concept_masteries.length} concepts
                </button>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Sessions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {student.recent_sessions.slice(0, 5).map((session) => (
                  <div key={session.id} className="flex justify-between items-center py-2 border-b last:border-0">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {new Date(session.started_at).toLocaleDateString()}
                      </div>
                      <div className="text-xs text-gray-500">
                        {session.message_count} messages
                      </div>
                    </div>
                    <div className="text-xs text-gray-400">
                      {session.concepts_covered.slice(0, 2).join(', ')}
                      {session.concepts_covered.length > 2 && ` +${session.concepts_covered.length - 2}`}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'mastery' && (
        <Card>
          <CardHeader>
            <CardTitle>Concept Mastery</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {student.concept_masteries.map((concept) => (
                <div key={concept.concept_id} className="border-b pb-4 last:border-0">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-medium text-gray-900">{concept.concept_name}</div>
                      <div className="text-xs text-gray-500">
                        {concept.attempts} attempts
                        {concept.last_interaction && (
                          <> &middot; Last: {new Date(concept.last_interaction).toLocaleDateString()}</>
                        )}
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-sm font-medium ${
                      concept.mastery_level >= 0.8 ? 'bg-green-100 text-green-700' :
                      concept.mastery_level >= 0.6 ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {Math.round(concept.mastery_level * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${getMasteryColor(concept.mastery_level)}`}
                      style={{ width: `${concept.mastery_level * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'sessions' && (
        <Card>
          <CardHeader>
            <CardTitle>Session History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {student.recent_sessions.map((session) => (
                <div key={session.id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium text-gray-900">
                        {new Date(session.started_at).toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-500 mt-1">
                        {session.message_count} messages
                        {session.ended_at && (
                          <> &middot; Duration: {Math.round(
                            (new Date(session.ended_at).getTime() - new Date(session.started_at).getTime()) / 60000
                          )} min</>
                        )}
                      </div>
                    </div>
                    <Button variant="outline" size="sm">View Transcript</Button>
                  </div>
                  {session.concepts_covered.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {session.concepts_covered.map((concept) => (
                        <span key={concept} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                          {concept}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'flags' && (
        <Card>
          <CardHeader>
            <CardTitle>Gaming Detection Flags</CardTitle>
          </CardHeader>
          <CardContent>
            {student.gaming_flags.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No gaming flags detected</p>
            ) : (
              <div className="space-y-4">
                {student.gaming_flags.map((flag) => (
                  <div key={flag.id} className={`p-4 rounded-lg ${getSeverityColor(flag.severity)}`}>
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium">{flag.signal_type}</div>
                        <div className="text-sm mt-1">{flag.details}</div>
                      </div>
                      <div className="text-xs">
                        {new Date(flag.detected_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
