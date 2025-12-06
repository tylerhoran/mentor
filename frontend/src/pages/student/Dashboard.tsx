import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/client';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { useAuthStore } from '../../stores/auth';

interface EnrolledCourse {
  id: string;
  name: string;
  code: string;
  instructor_name: string;
  enrolled_at: string;
  overall_mastery: number;
  concepts_mastered: number;
  total_concepts: number;
  last_session: string | null;
}

export default function StudentDashboard() {
  const { user } = useAuthStore();

  const { data: courses, isLoading } = useQuery({
    queryKey: ['enrolledCourses'],
    queryFn: () => api.get<EnrolledCourse[]>('/students/courses'),
  });

  const getMasteryColor = (level: number) => {
    if (level >= 0.8) return 'bg-green-500';
    if (level >= 0.6) return 'bg-yellow-500';
    if (level >= 0.4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}!
        </h1>
        <p className="text-gray-500">Continue your learning journey</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : !courses?.length ? (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="text-4xl mb-4">📚</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No courses yet</h3>
            <p className="text-gray-500 mb-4">
              You're not enrolled in any courses. Ask your instructor for an enrollment code.
            </p>
            <Button variant="outline">Enter Enrollment Code</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {courses.slice(0, 3).map((course) => (
              <Link
                key={course.id}
                to={`/student/courses/${course.id}/tutor`}
                className="block p-4 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg text-white hover:from-blue-600 hover:to-blue-700 transition-colors"
              >
                <div className="text-sm opacity-80">{course.code}</div>
                <div className="font-semibold text-lg mb-2">{course.name}</div>
                <div className="flex items-center justify-between">
                  <span className="text-sm opacity-80">Continue Learning</span>
                  <span className="text-xl">&rarr;</span>
                </div>
              </Link>
            ))}
          </div>

          {/* Course List */}
          <Card>
            <CardHeader>
              <CardTitle>My Courses</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {courses.map((course) => (
                  <div
                    key={course.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <div>
                          <h3 className="font-medium text-gray-900">{course.name}</h3>
                          <p className="text-sm text-gray-500">
                            {course.code} &middot; {course.instructor_name}
                          </p>
                        </div>
                      </div>
                      <div className="mt-3 flex items-center gap-4">
                        <div className="flex-1 max-w-xs">
                          <div className="flex justify-between text-xs text-gray-500 mb-1">
                            <span>Progress</span>
                            <span>{Math.round(course.overall_mastery * 100)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${getMasteryColor(course.overall_mastery)}`}
                              style={{ width: `${course.overall_mastery * 100}%` }}
                            />
                          </div>
                        </div>
                        <div className="text-sm text-gray-500">
                          {course.concepts_mastered}/{course.total_concepts} concepts
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <Link to={`/student/courses/${course.id}/progress`}>
                        <Button variant="outline" size="sm">Progress</Button>
                      </Link>
                      <Link to={`/student/courses/${course.id}/history`}>
                        <Button variant="outline" size="sm">History</Button>
                      </Link>
                      <Link to={`/student/courses/${course.id}/tutor`}>
                        <Button size="sm">Learn</Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {courses
                  .filter(c => c.last_session)
                  .sort((a, b) => new Date(b.last_session!).getTime() - new Date(a.last_session!).getTime())
                  .slice(0, 5)
                  .map((course) => (
                    <div key={course.id} className="flex items-center justify-between py-2 border-b last:border-0">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{course.name}</div>
                        <div className="text-xs text-gray-500">
                          Last session: {new Date(course.last_session!).toLocaleDateString()}
                        </div>
                      </div>
                      <Link
                        to={`/student/courses/${course.id}/tutor`}
                        className="text-blue-600 text-sm hover:underline"
                      >
                        Continue
                      </Link>
                    </div>
                  ))}
                {!courses.some(c => c.last_session) && (
                  <p className="text-gray-500 text-center py-4">No recent activity</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
