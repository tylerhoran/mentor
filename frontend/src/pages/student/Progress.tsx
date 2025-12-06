import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/client';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';

interface StudentProgress {
  course_id: string;
  course_name: string;
  overall_mastery: number;
  total_time_minutes: number;
  total_interactions: number;
  concepts: ConceptProgress[];
  learning_trajectory: TrajectoryPoint[];
  strengths: string[];
  areas_for_improvement: string[];
}

interface ConceptProgress {
  id: string;
  name: string;
  description: string;
  mastery_level: number;
  attempts: number;
  last_practiced: string | null;
  prerequisites_met: boolean;
  is_unlocked: boolean;
}

interface TrajectoryPoint {
  date: string;
  mastery: number;
  concepts_practiced: number;
}

export default function Progress() {
  const { courseId } = useParams<{ courseId: string }>();

  const { data: progress, isLoading } = useQuery({
    queryKey: ['studentProgress', courseId],
    queryFn: () => api.get<StudentProgress>(`/students/progress/${courseId}`),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!progress) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Progress data not available</p>
      </div>
    );
  }

  const getMasteryColor = (level: number) => {
    if (level >= 0.8) return 'bg-green-500';
    if (level >= 0.6) return 'bg-yellow-500';
    if (level >= 0.4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getMasteryLabel = (level: number) => {
    if (level >= 0.8) return 'Mastered';
    if (level >= 0.6) return 'Proficient';
    if (level >= 0.4) return 'Developing';
    if (level >= 0.2) return 'Beginning';
    return 'Not Started';
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6">
        <Link to="/student" className="text-blue-600 hover:underline text-sm">
          &larr; Back to Dashboard
        </Link>
      </div>

      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Progress</h1>
          <p className="text-gray-500">{progress.course_name}</p>
        </div>
        <Link to={`/student/courses/${courseId}/tutor`}>
          <Button>Continue Learning</Button>
        </Link>
      </div>

      {/* Overall Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-gray-900">
              {Math.round(progress.overall_mastery * 100)}%
            </div>
            <div className="text-sm text-gray-500">Overall Mastery</div>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${getMasteryColor(progress.overall_mastery)}`}
                style={{ width: `${progress.overall_mastery * 100}%` }}
              />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-gray-900">
              {progress.concepts.filter(c => c.mastery_level >= 0.8).length}
              <span className="text-lg font-normal text-gray-400">/{progress.concepts.length}</span>
            </div>
            <div className="text-sm text-gray-500">Concepts Mastered</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-gray-900">{progress.total_time_minutes}</div>
            <div className="text-sm text-gray-500">Minutes Learning</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-gray-900">{progress.total_interactions}</div>
            <div className="text-sm text-gray-500">Interactions</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Learning Trajectory */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Learning Trajectory</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48 flex items-end justify-between gap-1">
              {progress.learning_trajectory.map((point, idx) => {
                const height = point.mastery * 100;
                return (
                  <div key={idx} className="flex-1 flex flex-col items-center">
                    <div
                      className="w-full bg-blue-500 rounded-t transition-all"
                      style={{ height: `${height}%`, minHeight: point.mastery > 0 ? '4px' : '0' }}
                      title={`${new Date(point.date).toLocaleDateString()}: ${Math.round(point.mastery * 100)}% mastery`}
                    />
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between text-xs text-gray-400 mt-2">
              <span>
                {progress.learning_trajectory.length > 0 &&
                  new Date(progress.learning_trajectory[0].date).toLocaleDateString()}
              </span>
              <span>
                {progress.learning_trajectory.length > 0 &&
                  new Date(progress.learning_trajectory[progress.learning_trajectory.length - 1].date).toLocaleDateString()}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Strengths & Improvements */}
        <Card>
          <CardHeader>
            <CardTitle>Insights</CardTitle>
          </CardHeader>
          <CardContent>
            {progress.strengths.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-green-700 mb-2">Strengths</h4>
                <ul className="space-y-1">
                  {progress.strengths.map((strength, idx) => (
                    <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                      <span className="text-green-500">+</span>
                      {strength}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {progress.areas_for_improvement.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-orange-700 mb-2">Focus Areas</h4>
                <ul className="space-y-1">
                  {progress.areas_for_improvement.map((area, idx) => (
                    <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                      <span className="text-orange-500">!</span>
                      {area}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Concept Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Concept Mastery</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {progress.concepts.map((concept) => (
              <div
                key={concept.id}
                className={`p-4 border rounded-lg ${
                  concept.is_unlocked ? 'bg-white' : 'bg-gray-50 opacity-60'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{concept.name}</h4>
                  {!concept.is_unlocked && (
                    <span className="text-xs text-gray-400">Locked</span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mb-3 line-clamp-2">{concept.description}</p>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className={`font-medium ${
                      concept.mastery_level >= 0.8 ? 'text-green-600' :
                      concept.mastery_level >= 0.6 ? 'text-yellow-600' :
                      concept.mastery_level >= 0.4 ? 'text-orange-600' :
                      'text-gray-600'
                    }`}>
                      {getMasteryLabel(concept.mastery_level)}
                    </span>
                    <span className="text-gray-400">{Math.round(concept.mastery_level * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${getMasteryColor(concept.mastery_level)}`}
                      style={{ width: `${concept.mastery_level * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-400">
                    <span>{concept.attempts} attempts</span>
                    {concept.last_practiced && (
                      <span>Last: {new Date(concept.last_practiced).toLocaleDateString()}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
