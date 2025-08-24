import { NavigationMenu, NavigationMenuItem, NavigationMenuList } from "../ui/navigation-menu"
import { Search } from "lucide-react"
import { Link } from "react-router-dom"
import { useState } from "react"
import { Input } from "../ui/input"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog"

export function Navbar() {
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: Implement search functionality
    console.log("Searching for:", searchQuery)
    setIsSearchOpen(false)
  }

  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold">
          Horizons_code
        </Link>
        <NavigationMenu>
          <NavigationMenuList>
            <NavigationMenuItem>
              <Link to="/screening" className="px-4 py-2">
                スクリーニング
              </Link>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <Link to="/company-comparison" className="px-4 py-2">
                企業比較
              </Link>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <Link to="/financial-reports" className="px-4 py-2">
                決算資料
              </Link>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <Link to="/earnings-calendar" className="px-4 py-2">
                決算カレンダー
              </Link>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <Dialog open={isSearchOpen} onOpenChange={setIsSearchOpen}>
                <DialogTrigger asChild>
                  <button className="p-2">
                    <Search className="h-5 w-5" />
                  </button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>企業検索</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleSearch} className="space-y-4">
                    <Input
                      type="text"
                      placeholder="企業名または証券コードを入力"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </form>
                </DialogContent>
              </Dialog>
            </NavigationMenuItem>
          </NavigationMenuList>
        </NavigationMenu>
      </div>
    </header>
  )
}
