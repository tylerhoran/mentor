import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/client';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';

interface SessionHistory {
  sessions: Session[];
  total_count: number;
  page: number;
  page_size: number;
}

interface Session {
  id: string;
  started_at: string;
  ended_at: string | null;
  duration_minutes: number;
  message_count: number;
  concepts_covered: ConceptCovered[];
  mastery_changes: MasteryChange[];
  summary?: string;
}

interface ConceptCovered {
  id: string;
  name: string;
}

interface MasteryChange {
  concept_id: string;
  concept_name: string;
  before: number;
  after: number;
}

interface SessionDetail {
  id: string;
  started_at: string;
  ended_at: string | null;
  messages: Message[];
  concepts_covered: ConceptCovered[];
  mastery_changes: MasteryChange[];
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  pedagogical_move?: string;
}

export default function History() {
  const { courseId } = useParams<{ courseId: string }>();
  const [page, setPage] = useState(1);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);

  const { data: history, isLoading } = useQuery({
    queryKey: ['sessionHistory', courseId, page],
    queryFn: () => api.get<SessionHistory>(`/students/sessions/${courseId}?page=${page}&page_size=10`),
  });

  const { data: sessionDetail, isLoading: isLoadingDetail } = useQuery({
    queryKey: ['sessionDetail', selectedSession],
    queryFn: () => api.get<SessionDetail>(`/students/sessions/detail/${selectedSession}`),
    enabled: !!selectedSession,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6">
        <Link to="/student" className="text-blue-600 hover:underline text-sm">
          &larr; Back to Dashboard
        </Link>
      </div>

      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Session History</h1>
          <p className="text-gray-500">{history?.total_count || 0} sessions</p>
        </div>
        <Link to={`/student/courses/${courseId}/tutor`}>
          <Button>New Session</Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Session List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Sessions</CardTitle>
            </CardHeader>
            <CardContent>
              {!history?.sessions.length ? (
                <p className="text-gray-500 text-center py-8">No sessions yet</p>
              ) : (
                <div className="space-y-2">
                  {history.sessions.map((session) => (
                    <button
                      key={session.id}
                      onClick={() => setSelectedSession(session.id)}
                      className={`w-full text-left p-3 rounded-lg border transition-colors ${
                        selectedSession === session.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium text-gray-900">
                            {new Date(session.started_at).toLocaleDateString()}
                          </div>
                          <div className="text-xs text-gray-500">
                            {new Date(session.started_at).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-600">{session.message_count} msgs</div>
                          <div className="text-xs text-gray-400">{session.duration_minutes} min</div>
                        </div>
                      </div>
                      {session.concepts_covered.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {session.concepts_covered.slice(0, 2).map((concept) => (
                            <span
                              key={concept.id}
                              className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                            >
                              {concept.name}
                            </span>
                          ))}
                          {session.concepts_covered.length > 2 && (
                            <span className="text-xs text-gray-400">
                              +{session.concepts_covered.length - 2}
                            </span>
                          )}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              )}

              {/* Pagination */}
              {history && history.total_count > history.page_size && (
                <div className="flex justify-between items-center mt-4 pt-4 border-t">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-gray-500">
                    Page {page} of {Math.ceil(history.total_count / history.page_size)}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => p + 1)}
                    disabled={page * history.page_size >= history.total_count}
                  >
                    Next
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Session Detail */}
        <div className="lg:col-span-2">
          {!selectedSession ? (
            <Card>
              <CardContent className="py-12">
                <p className="text-gray-500 text-center">Select a session to view details</p>
              </CardContent>
            </Card>
          ) : isLoadingDetail ? (
            <Card>
              <CardContent className="py-12">
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
                </div>
              </CardContent>
            </Card>
          ) : sessionDetail ? (
            <div className="space-y-6">
              {/* Session Info */}
              <Card>
                <CardHeader>
                  <CardTitle>Session Details</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-sm text-gray-500">Started</div>
                      <div className="font-medium">
                        {new Date(sessionDetail.started_at).toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Duration</div>
                      <div className="font-medium">
                        {sessionDetail.ended_at
                          ? `${Math.round((new Date(sessionDetail.ended_at).getTime() - new Date(sessionDetail.started_at).getTime()) / 60000)} min`
                          : 'In progress'}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Messages</div>
                      <div className="font-medium">{sessionDetail.messages.length}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Concepts</div>
                      <div className="font-medium">{sessionDetail.concepts_covered.length}</div>
                    </div>
                  </div>

                  {/* Mastery Changes */}
                  {sessionDetail.mastery_changes.length > 0 && (
                    <div className="mt-4 pt-4 border-t">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Mastery Changes</h4>
                      <div className="flex flex-wrap gap-2">
                        {sessionDetail.mastery_changes.map((change) => (
                          <div
                            key={change.concept_id}
                            className={`px-2 py-1 rounded text-xs ${
                              change.after > change.before
                                ? 'bg-green-100 text-green-700'
                                : change.after < change.before
                                ? 'bg-red-100 text-red-700'
                                : 'bg-gray-100 text-gray-700'
                            }`}
                          >
                            {change.concept_name}: {Math.round(change.before * 100)}% → {Math.round(change.after * 100)}%
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Transcript */}
              <Card>
                <CardHeader>
                  <CardTitle>Transcript</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {sessionDetail.messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[80%] rounded-lg px-4 py-3 ${
                            message.role === 'user'
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-100 text-gray-900'
                          }`}
                        >
                          <div className="text-xs opacity-70 mb-1">
                            {new Date(message.timestamp).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </div>
                          <div className="whitespace-pre-wrap">{message.content}</div>
                          {message.pedagogical_move && (
                            <div className="mt-2 pt-2 border-t border-gray-300 text-xs opacity-70">
                              Move: {message.pedagogical_move}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
